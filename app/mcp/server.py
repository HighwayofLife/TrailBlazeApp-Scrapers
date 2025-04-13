"""
Model Context Protocol (MCP) server implementation for PostgreSQL database.

This module implements the MCP server that connects to your PostgreSQL database
and allows AI models to interact with your database in a controlled manner.
"""

import os
from typing import Dict, Any, List, Optional, Tuple
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, Field
import uvicorn

from app.database import DatabaseManager
from app.config import get_db_config
from app.logging_manager import get_logger

# Initialize logger
logger = get_logger(__name__).logger


# Models for MCP Protocol
class QueryRequest(BaseModel):
    """Model for a SQL query request."""
    query: str = Field(..., description="SQL query to execute")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Query parameters")


class QueryResponse(BaseModel):
    """Model for a SQL query response."""
    columns: List[str]
    rows: List[List[Any]]


class TablesRequest(BaseModel):
    """Model for a request to list database tables."""
    schema: Optional[str] = Field(None, description="Database schema")


class TableInfo(BaseModel):
    """Model for table information."""
    name: str
    schema: str


class TablesResponse(BaseModel):
    """Model for a response listing database tables."""
    tables: List[TableInfo]


class SchemaRequest(BaseModel):
    """Model for a request to get table schema."""
    table: str
    schema: Optional[str] = Field(None, description="Database schema")


class ColumnInfo(BaseModel):
    """Model for column information."""
    name: str
    type: str
    nullable: bool


class SchemaResponse(BaseModel):
    """Model for a response with table schema information."""
    columns: List[ColumnInfo]


# Database service
class PostgreSQLService:
    """Service for interacting with PostgreSQL database."""

    def __init__(self):
        """Initialize the PostgreSQL service."""
        self.db_manager = DatabaseManager(get_db_config())

    async def execute_query(
        self, query: str, parameters: Optional[Dict[str, Any]] = None
    ) -> Tuple[List[str], List[List[Any]]]:
        """
        Execute a SQL query and return results.

        Args:
            query: SQL query string
            parameters: Optional query parameters

        Returns:
            Tuple containing column names and result rows
        """
        if parameters is None:
            parameters = {}

        with self.db_manager.connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, parameters)
                if cursor.description:
                    columns = [desc[0] for desc in cursor.description]
                    rows = cursor.fetchall()
                    # Convert any non-serializable types to strings
                    rows = [[str(cell) if not isinstance(cell, (int, float, str, bool, type(None)))
                            else cell for cell in row] for row in rows]
                    return columns, rows
                return [], []

    async def get_tables(self, schema: Optional[str] = None) -> List[Dict[str, str]]:
        """
        Get list of tables in the database.

        Args:
            schema: Optional schema name

        Returns:
            List of tables with schema information
        """
        query = """
        SELECT table_name, table_schema
        FROM information_schema.tables
        WHERE table_type = 'BASE TABLE'
        """

        params = {}
        if schema:
            query += " AND table_schema = %(schema)s"
            params['schema'] = schema
        else:
            query += " AND table_schema NOT IN ('pg_catalog', 'information_schema')"

        _, rows = await self.execute_query(query, params)
        return [{"name": row[0], "schema": row[1]} for row in rows]

    async def get_table_schema(
        self, table: str, schema: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get schema information for a table.

        Args:
            table: Table name
            schema: Optional schema name

        Returns:
            List of column information dictionaries
        """
        query = """
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_name = %(table)s
        """

        params = {'table': table}
        if schema:
            query += " AND table_schema = %(schema)s"
            params['schema'] = schema

        _, rows = await self.execute_query(query, params)
        return [
            {
                "name": row[0],
                "type": row[1],
                "nullable": row[2].lower() == 'yes'
            }
            for row in rows
        ]


# Initialize FastAPI with lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for the FastAPI app.
    This function is called when the app starts and stops.
    It can be used to set up and tear down resources.

    Args:
        app: FastAPI application instance
    """
    # Setup tasks
    logger.info("Starting MCP PostgreSQL server")
    yield
    # Cleanup tasks
    logger.info("Shutting down MCP PostgreSQL server")


# Create FastAPI app
app = FastAPI(
    title="TrailBlazeApp PostgreSQL MCP Server",
    description="MCP server for PostgreSQL database integration",
    version="1.0.0",
    lifespan=lifespan
)


# Dependency for the database service
def get_db_service():
    """Dependency to get database service instance."""
    return PostgreSQLService()


@app.get("/")
async def root():
    """Health check endpoint."""
    return {"status": "ok", "message": "PostgreSQL MCP server is running"}


@app.post("/query", response_model=QueryResponse)
async def execute_query(
    request: QueryRequest, db_service: PostgreSQLService = Depends(get_db_service)
):
    """
    Execute SQL query on the PostgreSQL database.

    Args:
        request: Query request with SQL and parameters
        db_service: Database service dependency

    Returns:
        Query results with columns and rows
    """
    try:
        columns, rows = await db_service.execute_query(request.query, request.parameters)
        return QueryResponse(columns=columns, rows=rows)
    except Exception as e:
        logger.error(f"Error executing query: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/tables", response_model=TablesResponse)
async def get_tables(
    request: TablesRequest, db_service: PostgreSQLService = Depends(get_db_service)
):
    """
    Get list of tables in the database.

    Args:
        request: Tables request with optional schema
        db_service: Database service dependency

    Returns:
        List of tables with schema information
    """
    try:
        tables = await db_service.get_tables(request.schema)
        return TablesResponse(tables=[TableInfo(**table) for table in tables])
    except Exception as e:
        logger.error(f"Error getting tables: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/schema", response_model=SchemaResponse)
async def get_schema(
    request: SchemaRequest, db_service: PostgreSQLService = Depends(get_db_service)
):
    """
    Get schema information for a table.

    Args:
        request: Schema request with table name and optional schema
        db_service: Database service dependency

    Returns:
        Table schema with column information
    """
    try:
        columns = await db_service.get_table_schema(request.table, request.schema)
        return SchemaResponse(columns=[ColumnInfo(**col) for col in columns])
    except Exception as e:
        logger.error(f"Error getting schema: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


# Main entry point
def start_server(server_host: str = "0.0.0.0", server_port: int = 8000):
    """
    Start the MCP server.

    Args:
        server_host: Host to bind the server to
        server_port: Port to bind the server to
    """
    logger.info(f"Starting MCP PostgreSQL server on {server_host}:{server_port}")
    uvicorn.run(app, host=server_host, port=server_port)


if __name__ == "__main__":
    # Get host and port from environment variables or use defaults
    host = os.environ.get("MCP_HOST", "0.0.0.0")
    port = int(os.environ.get("MCP_PORT", 8001))
    start_server(server_host=host, server_port=port)

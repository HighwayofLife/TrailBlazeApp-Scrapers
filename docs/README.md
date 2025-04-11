# Documentation Index

Welcome to the TrailBlazeApp-Scrapers documentation. This index provides an overview of all available documentation, grouped by topic for easy navigation.

---

## 📚 Table of Contents

### **Getting Started**
- [Project Overview](../README.md): What this project is, its goals, and how to get started.
- [Quickstart & Usage](../README.md#quickstart): How to install dependencies, configure, and run the AERC scraper.

### **Scraping**
- [Scraping Guide (AERC)](development/scraping_guide.md): Step-by-step instructions for scraping the AERC calendar, including data structure, caching, and parsing logic.
- [Scraper Class Design](development/scraper_class.md): Details on the base scraper class and how to implement new scrapers.

### **Development**
- [Development Guide](development/development_guide.md): Best practices, environment setup, and development workflow.
- [Coding Rules](development/coding_rules.md): Coding standards and conventions for contributors.
- [Phased Development Plan](development/phased_development.md): Roadmap and phased approach for building out the project.

### **Architecture & Structure**
- [Project Structure](development/structure.md): Overview of the codebase organization and modular design.
- [Database Schema](schema.md): Details of the database schema and ORM models.

### **Data Handling & Validation**
- [Data Validation](development/data_validation.md): How to validate that scraped data matches what is stored in the database.
- [Data Handler Class](development/data_handler_class.md): Design and usage of the data handler for database operations.

### **Metrics, Logging, and Caching**
- [Metrics & Logging](development/metrics_and_logging.md): How metrics are tracked and logs are managed.
- [Cache Class](development/cache_class.md): Implementation and usage of the caching layer.

### **Testing**
- [Testing & TDD Guide](development/tdd_guide_and_class.md): Test-driven development workflow and test suite organization.

### **Analysis & Reviews**
- [Codebase Analysis](CODEBASE_ANALYSIS.md): Strengths, weaknesses, and recommendations for the codebase.
- [Application Review](development/applicaiton_review.md): High-level review of the application.

### **MCP Server**
- [MCP Server Overview](../app/mcp/server.py): FastAPI-based microservice for database access (see code and inline docs).

---

For any questions or contributions, please refer to the [Development Guide](development/development_guide.md).

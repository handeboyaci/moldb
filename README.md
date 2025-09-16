# moldb: Chemical Molecule Management API

moldb is a FastAPI-based application designed for managing and searching chemical molecules. It leverages PostgreSQL with the RDKit extension for efficient storage and retrieval of chemical structures, enabling various search functionalities.

## Features

*   **Molecule Management:** Store and retrieve chemical molecules with their properties (InChI, InChIKey, SMILES, molecular weight, chemical formula, LogP, TPSA, H-bond donors/acceptors, rotatable bonds, Morgan fingerprint).
*   **Asynchronous API:** Long-running tasks such as molecule creation and search are handled asynchronously by a background worker, providing a non-blocking API.
*   **Molecular Search:**
    *   Search by molecular weight range.
    *   Search by LogP range.
    *   Search by TPSA range.
    *   Search by number of H-bond donors range.
    *   Search by number of H-bond acceptors range.
    *   Search by number of rotatable bonds range.
    *   Search by exact match for InChI, InChIKey, SMILES, and chemical formula.
    *   Similarity search based on chemical fingerprints.
    *   Substructure search to find molecules containing a specific substructure.
*   **FastAPI:** Provides a modern, fast (high-performance) web framework for building APIs.
*   **PostgreSQL with RDKit:** Utilizes a robust relational database with the RDKit extension for cheminformatics capabilities, integrated using custom SQLAlchemy types.
*   **Dockerized:** Easily deployable and runnable using Docker and Docker Compose.
*   **Improved Error Handling:** Graceful handling of duplicate molecule creation attempts, returning a `409 Conflict` status.

## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes.

### Prerequisites

You need to have Docker and Docker Compose installed on your system.

*   [Docker Installation Guide](https://docs.docker.com/get-docker/)
*   Docker Compose is usually installed with Docker Desktop or can be installed separately.

### Running the Application

1.  **Clone the repository:**
    ```bash
    git clone <repository_url>
    cd moldb
    ```

2.  **Build and start the Docker containers:**
    This command will build the application image, set up the PostgreSQL and Redis services, and start everything in detached mode.
    ```bash
    docker compose up -d --build
    ```

3.  **Verify the application is running:**
    You can check the health endpoint of the FastAPI application.
    ```bash
    curl http://localhost:8000/health
    ```
    You should see `{"status":"ok"}` as the response.

The application API will be accessible at `http://localhost:8000`. You can explore the API documentation at `http://localhost:8000/docs` (Swagger UI) or `http://localhost:8000/redoc` (ReDoc).

## API Endpoints

Here are detailed examples of how to interact with the API endpoints using `curl`.

### 1. Create Molecule (`POST /api/v1/molecule`)

Creates a new chemical molecule in the database asynchronously.

**Request:**
```bash
curl -X POST \
  http://localhost:8000/api/v1/molecule \
  -H 'Content-Type: application/json' \
  -d 
  {
    "smiles": "CCO"
  }
```

**Successful Response (HTTP 202 Accepted):**
```json
{
  "job_id": "..."
}
```

### 2. Get Job Status (`GET /api/v1/jobs/{job_id}`)

Retrieves the status and result of a background job.

**Request:**
```bash
curl http://localhost:8000/api/v1/jobs/{job_id}
```

**Successful Response (HTTP 200 OK):**
```json
{
  "job_id": "...",
  "status": "finished",
  "result": {
    "id": "...",
    "inchi": "InChI=1S/C2H6O/c1-2-3/h3H,2H2,1H3",
    "inchikey": "LFQSCWFLJHTTHZ-UHFFFAOYSA-N",
    "smiles": "CCO",
    "molecular_weight": 46.069,
    "chemical_formula": "C2H6O",
    "logp": -0.0014,
    "tpsa": 20.23,
    "h_bond_donors": 1,
    "h_bond_acceptors": 1,
    "rotatable_bonds": 0
  },
  "error": null
}
```

### 3. Search Molecules (`GET /api/v1/search`)

Searches for molecules based on various property filters. All parameters are optional.

**Request (No filters - returns all molecules):**
```bash
curl "http://localhost:8000/api/v1/search"
```

**Request (Filter by molecular weight range):**
```bash
curl "http://localhost:8000/api/v1/search?min_mol_weight=40&max_mol_weight=50"
```

### 4. Find Similar Molecules (`POST /api/v1/search/similar`)

Finds molecules in the database similar to a given SMILES string based on Tanimoto similarity of Morgan fingerprints.

**Request:**
```bash
curl -X POST \
  http://localhost:8000/api/v1/search/similar \
  -H 'Content-Type: application/json' \
  -d 
  {
    "smiles": "CCO",
    "min_similarity": 0.7
  }
```

### 5. Substructure Search (`POST /api/v1/search/substructure`)

Finds molecules in the database that contain a given substructure (provided as a SMILES string).

**Request:**
```bash
curl -X POST \
  http://localhost:8000/api/v1/search/substructure \
  -H 'Content-Type: application/json' \
  -d 
  {
    "smiles": "C"
  }
```

## Running Tests

To run the automated tests for the application, follow these steps:

1.  **Ensure Docker services are running:**
    If not already running, start them:
    ```bash
    docker compose up -d
    ```

2.  **Execute the tests:**
    Now you can run the pytest suite within the `app` container.
    ```bash
    docker compose exec app pytest
    ```

    All tests should pass.

## Project Structure

```
.
├── alembic/                 # Alembic migration scripts
├── src/
│   ├── app/                 # Source code for the FastAPI application
│   │   ├── config.py        # Application configuration
│   │   ├── database.py      # Database session management
│   │   ├── database_types.py# Custom SQLAlchemy types for RDKit integration
│   │   ├── dependencies.py  # Dependency injection for FastAPI
│   │   ├── main.py          # Main FastAPI application
│   │   ├── models/          # SQLAlchemy models (e.g., molecule.py)
│   │   ├── repositories/    # Data access layer
│   │   ├── routers/         # API endpoints (e.g., molecules.py)
│   │   └── services/        # Business logic
│   └── worker/              # Background worker
├── tests/                   # Unit and integration tests
├── .gitignore
├── alembic.ini              # Alembic configuration
├── docker-compose.yml       # Docker Compose setup
├── Dockerfile               # Dockerfile for the application
├── entrypoint.sh            # Entrypoint script for the application container
├── pytest.ini               # Pytest configuration
├── requirements.txt         # Python dependencies
└── ruff.toml                # Ruff linter configuration
```

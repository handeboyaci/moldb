import os
from sqlalchemy import create_engine, text
from src.app.models.molecule import Base

SQLALCHEMY_DATABASE_URL = "postgresql://user:password@db:5432/chemstructdb"
engine = create_engine(SQLALCHEMY_DATABASE_URL)

with engine.connect() as connection:
    connection.execute(text("CREATE EXTENSION IF NOT EXISTS rdkit"))
    connection.execute(
        text(
            """
        CREATE OR REPLACE FUNCTION update_molecule_data()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.mol = mol_from_smiles(NEW.smiles::cstring);
            NEW.morgan_fingerprint = morganbv_fp(NEW.mol);
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        """
        )
    )
    connection.commit()

Base.metadata.create_all(bind=engine)

with engine.connect() as connection:
    connection.execute(
        text(
            """
        CREATE TRIGGER update_molecule_data_trigger
        BEFORE INSERT OR UPDATE ON molecules
        FOR EACH ROW EXECUTE FUNCTION update_molecule_data();
        """
        )
    )
    connection.commit()

print("Tables created successfully.")
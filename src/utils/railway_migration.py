# ruff: noqa
import json
import sys
from typing import Any

import pandas as pd
from loguru import logger
from sqlalchemy import create_engine, exc, inspect, text
from sqlalchemy.dialects.postgresql import ARRAY, JSON, JSONB
from sqlalchemy.engine import Engine
from sqlalchemy.engine.reflection import Inspector
from sqlalchemy.exc import NoSuchTableError


class DatabaseMigrator:
    def __init__(
        self,
        source_url: str,
        target_url: str,
        tables: list[str] = None,  # type: ignore
    ):
        logger.info("🚀 Initializing database migrator...")
        source_url = source_url.replace("postgres://", "postgresql://")
        target_url = target_url.replace("postgres://", "postgresql://")

        self.source_engine = create_engine(source_url)
        self.target_engine = create_engine(target_url)

        self.tables = tables or [
            "investors",
            "investor_chunks",
            "team_members",
            "portfolio_companies",
        ]
        self.batch_size = 1000
        logger.success("✨ Migrator initialized successfully")

    def validate_table_name(self, engine: Engine, table_name: str) -> str:
        """Validate table exists in database before using in queries."""
        inspector = inspect(engine)
        if not inspector.has_table(table_name):
            raise NoSuchTableError(f"Table {table_name} does not exist")
        return table_name

    def get_table_structure(self, engine: Engine, table_name: str) -> dict[str, Any]:
        """Extract table structure including column types."""
        validated_table = self.validate_table_name(engine, table_name)
        inspector: Inspector = inspect(engine)
        return {col["name"]: col["type"] for col in inspector.get_columns(validated_table)}

    def table_exists(self, table_name: str) -> bool:
        """Check if a table exists in the target database."""
        inspector = inspect(self.target_engine)
        return inspector.has_table(table_name)

    def clean_target_tables(self) -> None:
        """Clean target tables in reverse order to respect foreign keys."""
        logger.info("🧹 Cleaning target tables...")
        with self.target_engine.connect() as conn:
            try:
                conn.execute(text("SET CONSTRAINTS ALL DEFERRED;"))
                for table in reversed(self.tables):
                    validated_table = self.validate_table_name(self.target_engine, table)
                    logger.info(f"🗑️ Truncating table: {validated_table}")
                    conn.execute(text(f"TRUNCATE TABLE {validated_table} CASCADE;"))  # nosec B608
                conn.commit()
                logger.success("✨ Tables cleaned successfully")
            except Exception as e:
                conn.rollback()
                logger.error(f"❌ Error cleaning tables: {e!s}")
                raise

    def initialize_vector_extension(self) -> None:
        """Initialize the vector extension in the target database."""
        with self.target_engine.connect() as conn:
            try:
                conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
                conn.commit()
                logger.success("✅ Enabled vector extension")
            except Exception as e:
                logger.error(f"❌ Failed to enable vector extension: {e!s}")
                raise

    def get_column_type_string(self, col_type: Any, col_name: str) -> str:
        """Convert SQLAlchemy type to PostgreSQL type string."""
        if isinstance(col_type, ARRAY):
            element_type = str(col_type.item_type)  # type: ignore
            return "TEXT[]" if "TEXT" in element_type.upper() else "VARCHAR[]"
        elif isinstance(col_type, (JSON, JSONB)):
            return "JSONB"
        elif str(col_type) == "vector":
            return "vector(1536)"
        else:
            return str(col_type)

    def create_table_schema(self, table_name: str) -> None:
        """Create table schema in target database if it doesn't exist."""
        validated_table = self.validate_table_name(self.source_engine, table_name)
        inspector = inspect(self.source_engine)
        try:
            columns = inspector.get_columns(validated_table)
            constraints = inspector.get_pk_constraint(validated_table)
            foreign_keys = inspector.get_foreign_keys(validated_table)

            create_stmt = f"CREATE TABLE IF NOT EXISTS {validated_table} (\n"  # nosec B608
            column_defs = []

            for col in columns:
                col_name = col["name"]
                if col_name == "embedding":
                    col_type = "vector(1536)"
                else:
                    col_type = self.get_column_type_string(col["type"], col_name)
                nullable = "NULL" if col.get("nullable", True) else "NOT NULL"
                column_defs.append(f"    {col_name} {col_type} {nullable}")  # type: ignore

            if constraints and constraints.get("constrained_columns"):
                pk_cols = constraints["constrained_columns"]
                column_defs.append(f"    PRIMARY KEY ({', '.join(pk_cols)})")  # type: ignore

            for fk in foreign_keys:
                referred_table = fk["referred_table"]
                constrained_cols = fk["constrained_columns"]
                referred_cols = fk["referred_columns"]
                fk_name = fk.get("name", f"fk_{validated_table}_{referred_table}")
                column_defs.append(  # type: ignore
                    f"    CONSTRAINT {fk_name} FOREIGN KEY ({', '.join(constrained_cols)}) "
                    f"REFERENCES {referred_table} ({', '.join(referred_cols)})"
                )

            create_stmt += ",\n".join(column_defs)  # type: ignore
            create_stmt += "\n);"

            with self.target_engine.connect() as conn:
                conn.execute(text(create_stmt))
                conn.commit()
                logger.success(f"✅ Created schema for {validated_table}")
        except Exception as e:
            logger.error(f"❌ Error creating schema for {validated_table}: {e!s}")
            raise

    def preprocess_row(self, row: dict[str, Any], structure: dict[str, Any]) -> dict[str, Any]:
        """Preprocess row data to handle JSON and array fields."""
        processed: dict[str, Any] = {}
        for col, value in row.items():
            if col not in structure:
                continue

            col_type = structure[col]
            if isinstance(col_type, (JSON, JSONB)):
                if isinstance(value, (dict, list)):
                    processed[col] = json.dumps(value)
                elif isinstance(value, str):
                    try:
                        json.loads(value)
                        processed[col] = value
                    except json.JSONDecodeError:
                        processed[col] = json.dumps(value)
                else:
                    processed[col] = json.dumps(value) if value is not None else None
            elif isinstance(col_type, ARRAY):
                if isinstance(value, list):
                    processed[col] = value
                elif isinstance(value, str):
                    try:
                        processed[col] = json.loads(value)
                    except json.JSONDecodeError:
                        if value.startswith("{") and value.endswith("}"):
                            processed[col] = value[1:-1].split(",")
                        else:
                            processed[col] = [value] if value else []
                else:
                    processed[col] = [value] if value is not None else []
            else:
                processed[col] = value
        return processed

    def migrate_table(self, table_name: str) -> None:
        """Migrate a single table with progress bar."""
        validated_table = self.validate_table_name(self.source_engine, table_name)
        logger.info(f"📋 Starting migration of table: {validated_table}")

        source_structure = self.get_table_structure(self.source_engine, validated_table)

        # Safe count query
        count_query = text(f"SELECT COUNT(*) FROM {validated_table}")  # nosec B608
        with self.source_engine.connect() as conn:
            total_count = conn.execute(count_query).scalar()
        logger.info(f"📊 Found {total_count} rows in source table {validated_table}")

        connection = self.target_engine.connect()
        transaction = connection.begin()
        try:
            offset = 0
            total_rows = 0
            while True:
                # Safe query with parameter binding
                query = text(
                    f"SELECT * FROM {validated_table} "  # nosec B608
                    "LIMIT :limit OFFSET :offset"
                )
                params = {"limit": self.batch_size, "offset": offset}
                chunk: pd.DataFrame = pd.read_sql(query, self.source_engine, params=params)

                if chunk.empty:
                    break

                processed_data = []
                for _, row in chunk.iterrows():  # type: ignore
                    processed_row = self.preprocess_row(row.to_dict(), source_structure)  # type: ignore
                    processed_data.append(processed_row)

                if processed_data:
                    df = pd.DataFrame(processed_data)
                    df.to_sql(validated_table, connection, if_exists="append", index=False)

                    # Safe verification
                    verify_query = text(f"SELECT COUNT(*) FROM {validated_table}")  # nosec B608
                    current_count = connection.execute(verify_query).scalar()
                    logger.debug(f"✓ Current count in target table: {current_count}")

                offset += self.batch_size
                total_rows += len(chunk)
                logger.info(f"🔄 Migrated {total_rows} rows from {validated_table}...")

            # Final verification
            verify_query = text(f"SELECT COUNT(*) FROM {validated_table}")  # nosec B608
            final_count = connection.execute(verify_query).scalar()
            logger.info(f"📊 Final count in target table {validated_table}: {final_count}")

            transaction.commit()
            logger.success(f"✅ Successfully migrated {validated_table}")
        except exc.OperationalError as e:
            transaction.rollback()
            logger.error(f"❌ Database connection error while migrating {validated_table}: {e!s}")
            raise
        except exc.IntegrityError as e:
            transaction.rollback()
            logger.error(f"❌ Data integrity error while migrating {validated_table}: {e!s}")
            raise
        except Exception as e:
            transaction.rollback()
            logger.error(f"❌ Error migrating {validated_table}: {e!s}")
            logger.exception("Detailed error trace:")
            raise
        finally:
            connection.close()

    def migrate_all(self) -> None:
        """Migrate all specified tables."""
        logger.info("🎯 Starting migration of all tables")
        self.initialize_vector_extension()

        for table in self.tables:
            try:
                self.create_table_schema(table)
            except Exception as e:
                logger.error(f"❌ Failed to create schema for {table}: {e!s}")
                raise

        self.clean_target_tables()

        for table in self.tables:
            try:
                self.migrate_table(table)
            except Exception as e:
                logger.error(f"❌ Failed to migrate {table}: {e!s}")
                raise


def main():
    logger.remove()
    logger.add(
        sys.stderr,
        format="<white>{time:HH:mm:ss}</white> | <level>{level: <8}</level> | <level>{message}</level>",
        colorize=True,
        level="INFO",
    )
    logger.add(
        "migration_{time}.log",
        rotation="500 MB",
        level="DEBUG",
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    )

    SUPABASE_URL = "your_connection_string"
    RAILWAY_URL = "your_connection_string"

    try:
        migrator = DatabaseMigrator(source_url=SUPABASE_URL, target_url=RAILWAY_URL)
        migrator.migrate_all()
        logger.success("🎉 Migration completed successfully!")
    except Exception as e:
        logger.error(f"💥 Migration failed: {e!s}")
        logger.exception("Detailed error trace:")


if __name__ == "__main__":
    main()

# drop_all_tables.py - Drop all tables to start fresh

import pymysql
from app.config import settings

def drop_all_tables():
    connection = pymysql.connect(
        host=settings.DB_HOST,
        port=int(settings.DB_PORT),
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
        database=settings.DB_NAME
    )
    
    try:
        with connection.cursor() as cursor:
            print("\n🗑️  Dropping all tables...")
            
            # Disable foreign key checks
            cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
            
            # Get all tables
            cursor.execute("SHOW TABLES")
            tables = [row[0] for row in cursor.fetchall()]
            
            # Drop each table
            for table in tables:
                print(f"  Dropping {table}...")
                cursor.execute(f"DROP TABLE IF EXISTS `{table}`")
            
            # Re-enable foreign key checks
            cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
            
            connection.commit()
            print(f"\n✅ Dropped {len(tables)} tables successfully!")
            print("\nNow run: alembic upgrade head")
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        connection.rollback()
    finally:
        connection.close()


if __name__ == "__main__":
    drop_all_tables()

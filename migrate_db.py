#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script para migrar la base de datos local a Supabase usando psycopg2
"""

import os
import sys
import time
from pathlib import Path
import psycopg2
from psycopg2 import sql
from psycopg2.extras import execute_values
from dotenv import load_dotenv
import unidecode

# Cargar variables de entorno
load_dotenv()

# Configuración
LOCAL_DB_URL = 'postgresql://postgres:0000@localhost:5432/db_aguas_residuales_med'
SUPABASE_DB_URL = 'postgresql://postgres.pwchvabtkdmhkzjzlbhf:0000@aws-0-us-east-2.pooler.supabase.com:6543/postgres'

def normalize_text(text):
    """Normalizar texto para evitar problemas de codificación"""
    if text is None:
        return None
    if isinstance(text, str):
        return unidecode.unidecode(text)
    return text

def get_tables(conn):
    """Obtener lista de tablas en la base de datos"""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            AND table_type = 'BASE TABLE'
            AND table_name != 'spatial_ref_sys'
        """)
        return [row[0] for row in cur.fetchall()]

def check_problematic_chars(data):
    """Identificar caracteres problemáticos en los datos"""
    problematic_rows = []
    for i, row in enumerate(data):
        for j, value in enumerate(row):
            if isinstance(value, str):
                try:
                    value.encode('utf-8')
                except UnicodeEncodeError as e:
                    problematic_rows.append({
                        'row_index': i,
                        'column_index': j,
                        'value': value,
                        'error': str(e)
                    })
    return problematic_rows

def migrate_table(local_conn, supabase_conn, table_name):
    """Migrar una tabla específica"""
    print(f"\nMigrando tabla: {table_name}")
    
    try:
        # Obtener estructura de la tabla
        with local_conn.cursor() as cur:
            cur.execute(f"""
                SELECT column_name, data_type, character_maximum_length, udt_name
                FROM information_schema.columns
                WHERE table_name = '{table_name}'
                ORDER BY ordinal_position
            """)
            columns = cur.fetchall()
            
            # Obtener datos
            cur.execute(f"SELECT * FROM {table_name}")
            data = cur.fetchall()
            
            # Verificar caracteres problemáticos
            print(f"\nVerificando caracteres problemáticos en la tabla {table_name}...")
            problematic_chars = check_problematic_chars(data)
            if problematic_chars:
                print("\nSe encontraron caracteres problemáticos:")
                for prob in problematic_chars:
                    print(f"Fila {prob['row_index']}, Columna {prob['column_index']}:")
                    print(f"Valor: {prob['value']}")
                    print(f"Error: {prob['error']}\n")
                return False
        
        # Crear tabla en Supabase
        with supabase_conn.cursor() as cur:
            # Construir CREATE TABLE
            column_defs = []
            for col_name, data_type, max_length, udt_name in columns:
                # Escapar el nombre de la columna con comillas dobles si contiene espacios
                safe_col_name = f'"{col_name}"' if ' ' in col_name else col_name
                
                if udt_name == 'geometry':
                    col_def = f"{safe_col_name} geometry"
                elif udt_name == 'float8' or udt_name == 'double precision':
                    col_def = f"{safe_col_name} double precision"
                elif data_type == 'character varying' and max_length:
                    col_def = f"{safe_col_name} {data_type}({max_length})"
                else:
                    col_def = f"{safe_col_name} {data_type}"
                column_defs.append(col_def)
            
            # Crear tabla
            create_sql = f"""
                DROP TABLE IF EXISTS {table_name} CASCADE;
                CREATE TABLE {table_name} (
                    {', '.join(column_defs)}
                );
            """
            cur.execute(create_sql)
            supabase_conn.commit()
            
            # Insertar datos en lotes
            if data:
                # Escapar nombres de columnas con espacios
                columns_str = ', '.join([f'"{col[0]}"' if ' ' in col[0] else col[0] for col in columns])
                insert_sql = f"INSERT INTO {table_name} ({columns_str}) VALUES %s"
                
                batch_size = 1000
                for i in range(0, len(data), batch_size):
                    batch = data[i:i + batch_size]
                    try:
                        execute_values(cur, insert_sql, batch)
                        supabase_conn.commit()
                        print(f"  Migrados {min(i + batch_size, len(data))} registros de {len(data)}")
                    except Exception as e:
                        print(f"  Error en lote {i}-{i+batch_size}: {str(e)}")
                        # Intentar insertar registro por registro
                        for j, row in enumerate(batch):
                            try:
                                cur.execute(f"INSERT INTO {table_name} ({columns_str}) VALUES %s", (row,))
                                supabase_conn.commit()
                            except Exception as e2:
                                print(f"    Error en registro {i+j}: {str(e2)}")
                                continue
        
        print(f"Tabla {table_name} migrada exitosamente")
        return True
        
    except Exception as e:
        print(f"Error migrando tabla {table_name}: {str(e)}")
        return False

def migrate_database():
    """Migrar la base de datos local a Supabase"""
    print("Iniciando migración de base de datos...")
    
    try:
        # Conectar a ambas bases de datos
        local_conn = psycopg2.connect(LOCAL_DB_URL)
        supabase_conn = psycopg2.connect(SUPABASE_DB_URL)
        
        # Habilitar PostGIS en Supabase
        print("Habilitando PostGIS en Supabase...")
        with supabase_conn.cursor() as cur:
            cur.execute("CREATE EXTENSION IF NOT EXISTS postgis;")
            supabase_conn.commit()
        
        # Obtener lista de tablas
        tables = get_tables(local_conn)
        print(f"Tablas a migrar: {', '.join(tables)}")
        
        # Migrar cada tabla
        for table in tables:
            if not migrate_table(local_conn, supabase_conn, table):
                print(f"Error en la migración de la tabla {table}")
                return False
        
        print("\nMigración completada con éxito")
        return True
        
    except Exception as e:
        print(f"Error durante la migración: {str(e)}")
        return False
        
    finally:
        # Cerrar conexiones
        if 'local_conn' in locals():
            local_conn.close()
        if 'supabase_conn' in locals():
            supabase_conn.close()

if __name__ == "__main__":
    migrate_database() 
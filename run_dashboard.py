#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script para ejecutar el dashboard de Streamlit
"""

import os
import subprocess
import sys

def run_dashboard():
    """Ejecutar el dashboard de Streamlit"""
    try:
        # Obtener la ruta del directorio actual
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Cambiar al directorio del dashboard
        os.chdir(current_dir)
        
        # Ejecutar Streamlit
        subprocess.run([
            sys.executable,
            "-m",
            "streamlit",
            "run",
            "home.py",
            "--server.port=8501",
            "--server.address=0.0.0.0"
        ])
        
    except Exception as e:
        print(f"Error al ejecutar el dashboard: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    run_dashboard() 
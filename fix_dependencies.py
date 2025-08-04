#!/usr/bin/env python3
"""
Fix Dependencies - Herramienta de Diagnóstico y Reparación
=========================================================

Script especializado para resolver problemas de dependencias en Python 3.13
con instalaciones de usuario y sistema.

Autor: Dog Emotion AI Team
Versión: 1.0
"""

import sys
import os
import subprocess
import platform
import site
import importlib.util
from pathlib import Path
import json
from typing import Dict, List, Tuple
import shutil

class DependencyFixer:
    """Diagnóstica y repara problemas de dependencias"""
    
    def __init__(self):
        self.issues = []
        self.python_info = self._get_python_info()
        
    def _get_python_info(self) -> Dict:
        """Obtiene información detallada del entorno Python"""
        return {
            'version': sys.version,
            'executable': sys.executable,
            'platform': platform.platform(),
            'prefix': sys.prefix,
            'base_prefix': sys.base_prefix,
            'user_base': site.USER_BASE,
            'user_site': site.USER_SITE,
            'sys_path': sys.path,
            'site_packages': [p for p in sys.path if 'site-packages' in p]
        }
    
    def print_diagnostic_header(self):
        """Imprime información de diagnóstico"""
        print("=" * 70)
        print("🔍 DIAGNÓSTICO DEL SISTEMA PYTHON")
        print("=" * 70)
        print(f"🐍 Python: {sys.version.split()[0]}")
        print(f"📁 Ejecutable: {self.python_info['executable']}")
        print(f"💻 Sistema: {self.python_info['platform']}")
        print(f"📂 Prefijo: {self.python_info['prefix']}")
        print(f"👤 User Base: {self.python_info['user_base']}")
        print(f"📦 User Site: {self.python_info['user_site']}")
        print("\n📚 Rutas de site-packages encontradas:")
        for i, path in enumerate(self.python_info['site_packages'], 1):
            print(f"  {i}. {path}")
        print("=" * 70)
    
    def check_package_locations(self) -> Dict[str, List[str]]:
        """Verifica dónde están instalados los paquetes"""
        packages_to_check = {
            'cv2': 'opencv-python',
            'PIL': 'Pillow',
            'flask': 'flask',
            'flask_socketio': 'flask-socketio',
            'tensorflow': 'tensorflow',
            'numpy': 'numpy',
            'telegram': 'python-telegram-bot',
            'ultralytics': 'ultralytics'
        }
        
        package_locations = {}
        
        print("\n🔍 Buscando paquetes instalados...")
        print("-" * 50)
        
        for module_name, package_name in packages_to_check.items():
            locations = []
            spec = importlib.util.find_spec(module_name)
            
            if spec and spec.origin:
                locations.append(spec.origin)
                print(f"✅ {package_name}: {spec.origin}")
            else:
                print(f"❌ {package_name}: NO ENCONTRADO")
                self.issues.append(f"Paquete {package_name} no encontrado")
            
            package_locations[package_name] = locations
        
        return package_locations
    
    def fix_path_issues(self):
        """Corrige problemas de PATH"""
        print("\n🔧 Verificando problemas de PATH...")
        
        # Agregar user site-packages al PATH si no está
        user_site = site.USER_SITE
        if user_site and os.path.exists(user_site) and user_site not in sys.path:
            print(f"⚠️ User site-packages no está en sys.path: {user_site}")
            sys.path.insert(0, user_site)
            print(f"✅ Agregado al sys.path")
        
        # Verificar scripts de usuario
        user_scripts = Path(site.USER_BASE) / "Scripts" if os.name == 'nt' else Path(site.USER_BASE) / "bin"
        if user_scripts.exists():
            scripts_in_path = str(user_scripts) in os.environ.get('PATH', '')
            if not scripts_in_path:
                print(f"⚠️ Scripts de usuario no están en PATH: {user_scripts}")
                self.issues.append(f"Agregar al PATH: {user_scripts}")
    
    def check_pip_configuration(self):
        """Verifica la configuración de pip"""
        print("\n🔧 Verificando configuración de pip...")
        
        try:
            result = subprocess.run([sys.executable, "-m", "pip", "config", "list"], 
                                  capture_output=True, text=True)
            if result.stdout:
                print("📋 Configuración actual de pip:")
                print(result.stdout)
            else:
                print("✅ Sin configuración personalizada de pip")
        except Exception as e:
            print(f"⚠️ Error verificando pip config: {e}")
    
    def reinstall_problem_packages(self):
        """Reinstala paquetes problemáticos"""
        print("\n🔄 Paquetes que necesitan reinstalación:")
        
        problem_packages = ['opencv-python', 'Pillow']
        
        for package in problem_packages:
            print(f"\n📦 Reinstalando {package}...")
            try:
                # Desinstalar primero
                print(f"  🗑️ Desinstalando {package}...")
                subprocess.run([sys.executable, "-m", "pip", "uninstall", package, "-y"], 
                             check=True, capture_output=True)
                
                # Reinstalar con --user
                print(f"  📥 Instalando {package} con --user...")
                subprocess.run([sys.executable, "-m", "pip", "install", package, "--user", "--force-reinstall"], 
                             check=True, capture_output=True)
                
                print(f"  ✅ {package} reinstalado correctamente")
            except subprocess.CalledProcessError as e:
                print(f"  ❌ Error reinstalando {package}: {e}")
                self.issues.append(f"No se pudo reinstalar {package}")
    
    def create_import_test(self):
        """Crea un script de prueba de importación"""
        test_script = '''#!/usr/bin/env python3
"""Script de prueba de importaciones"""

import sys
print(f"Python: {sys.version}")
print(f"Ejecutable: {sys.executable}")
print("-" * 50)

packages = [
    ("cv2", "OpenCV"),
    ("PIL", "Pillow"),
    ("flask", "Flask"),
    ("tensorflow", "TensorFlow"),
    ("numpy", "NumPy"),
    ("telegram", "python-telegram-bot"),
    ("ultralytics", "Ultralytics")
]

for module_name, display_name in packages:
    try:
        module = __import__(module_name)
        version = getattr(module, "__version__", "Unknown")
        print(f"✅ {display_name}: {version}")
    except ImportError as e:
        print(f"❌ {display_name}: Error - {e}")

print("-" * 50)
input("Presiona Enter para continuar...")
'''
        
        test_file = Path("test_imports.py")
        test_file.write_text(test_script, encoding='utf-8')
        print(f"\n✅ Creado script de prueba: {test_file}")
        return test_file
    
    def create_environment_setup(self):
        """Crea un script de configuración del entorno"""
        setup_script = f'''@echo off
REM Script de configuración del entorno para Dog Emotion AI

echo ========================================
echo Configurando entorno para Dog Emotion AI
echo ========================================

REM Agregar rutas de Python al PATH
set PATH={self.python_info['user_base']}\\Scripts;%PATH%
set PYTHONPATH={self.python_info['user_site']};%PYTHONPATH%

REM Configurar TensorFlow
set TF_CPP_MIN_LOG_LEVEL=2

echo.
echo ✅ Entorno configurado correctamente
echo.
echo Ejecuta ahora: python main.py
echo.
pause
'''
        
        setup_file = Path("setup_environment.bat")
        setup_file.write_text(setup_script, encoding='utf-8')
        print(f"\n✅ Creado script de configuración: {setup_file}")
        return setup_file
    
    def generate_report(self):
        """Genera un reporte completo"""
        report = {
            'timestamp': str(Path().resolve()),
            'python_info': self.python_info,
            'issues_found': self.issues,
            'recommendations': []
        }
        
        if self.issues:
            report['recommendations'].append("Ejecutar: pip install --user -r requirements.txt")
            report['recommendations'].append("Usar el script setup_environment.bat antes de ejecutar main.py")
        
        report_file = Path("diagnostic_report.json")
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📄 Reporte guardado en: {report_file}")
    
    def run_full_diagnostic(self):
        """Ejecuta diagnóstico completo"""
        print("\n🚀 INICIANDO DIAGNÓSTICO COMPLETO")
        print("=" * 70)
        
        # 1. Información del sistema
        self.print_diagnostic_header()
        
        # 2. Verificar ubicación de paquetes
        package_locations = self.check_package_locations()
        
        # 3. Verificar problemas de PATH
        self.fix_path_issues()
        
        # 4. Verificar configuración de pip
        self.check_pip_configuration()
        
        # 5. Crear scripts de ayuda
        self.create_import_test()
        self.create_environment_setup()
        
        # 6. Generar reporte
        self.generate_report()
        
        # 7. Resumen final
        print("\n" + "=" * 70)
        print("📊 RESUMEN DEL DIAGNÓSTICO")
        print("=" * 70)
        
        if self.issues:
            print(f"⚠️ Se encontraron {len(self.issues)} problemas:")
            for issue in self.issues:
                print(f"  • {issue}")
            
            print("\n🔧 SOLUCIONES RECOMENDADAS:")
            print("1. Ejecuta: setup_environment.bat")
            print("2. Reinstala dependencias: pip install --user -r requirements.txt")
            print("3. Si persisten problemas con opencv/pillow:")
            print("   python fix_dependencies.py --reinstall")
        else:
            print("✅ No se encontraron problemas significativos")
        
        print("\n💡 Prueba las importaciones con: python test_imports.py")
        print("=" * 70)

def main():
    """Función principal"""
    fixer = DependencyFixer()
    
    if len(sys.argv) > 1 and sys.argv[1] == '--reinstall':
        print("🔄 Modo de reinstalación activado")
        fixer.reinstall_problem_packages()
    else:
        fixer.run_full_diagnostic()
    
    input("\nPresiona Enter para salir...")

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Validation script for Phase 2-3 indexing and filtering systems
Checks environment setup, dependencies, and basic functionality
"""

import os
import sys
import subprocess
import logging
from pathlib import Path
import importlib.util
import tempfile

def check_python_version():
    """Check Python version compatibility"""
    print("🔍 Checking Python version...")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        print(f"✅ Python {version.major}.{version.minor}.{version.micro} is supported")
        return True
    else:
        print(f"❌ Python 3.8+ required, found {version.major}.{version.minor}")
        return False

def check_dependencies():
    """Check required dependencies"""
    print("\n🔍 Checking dependencies...")
    
    required_packages = [
        'jieba', 'sklearn', 'transformers', 'torch', 'sentence-transformers',
        'bertopic', 'psycopg2', 'sqlalchemy', 'pandas', 'numpy', 'opencc'
    ]
    
    missing = []
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} - missing")
            missing.append(package)
    
    if missing:
        print(f"\n📦 Missing packages: {', '.join(missing)}")
        print("Install with: pip install -r phase2_indexing/requirements.txt")
        return False
    
    return True

def check_environment_variables():
    """Check required environment variables"""
    print("\n🔍 Checking environment variables...")
    
    required_vars = [
        'DATABASE_URL',
        'OPENAI_API_KEY'
    ]
    
    missing = []
    for var in required_vars:
        if os.getenv(var):
            print(f"✅ {var}: Set")
        else:
            print(f"❌ {var}: Not set")
            missing.append(var)
    
    if missing:
        print(f"\n📝 Missing environment variables: {', '.join(missing)}")
        print("Create .env file with these variables")
        return False
    
    return True

def check_filesystem():
    """Check filesystem setup"""
    print("\n🔍 Checking filesystem...")
    
    required_dirs = [
        'phase2_indexing',
        'phase3_filtering',
        'shared',
        'shared/database',
        'shared/utils',
        'shared/config'
    ]
    
    base_path = Path(__file__).parent
    missing_dirs = []
    
    for dir_path in required_dirs:
        full_path = base_path / dir_path
        if full_path.exists() and full_path.is_dir():
            print(f"✅ {dir_path}/")
        else:
            print(f"❌ {dir_path}/ - missing")
            missing_dirs.append(dir_path)
    
    # Check specific files
    required_files = [
        'phase2_indexing/keyword_indexer.py',
        'phase2_indexing/search_builder.py',
        'phase2_indexing/topic_clusterer.py',
        'phase3_filtering/content_filter.py',
        'shared/database/models.py',
        'shared/utils/file_helpers.py',
        'shared/config/phase2_config.py'
    ]
    
    missing_files = []
    for file_path in required_files:
        full_path = base_path / file_path
        if full_path.exists() and full_path.is_file():
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} - missing")
            missing_files.append(file_path)
    
    if missing_dirs or missing_files:
        return False
    
    return True

def check_database_connection():
    """Check database connectivity"""
    print("\n🔍 Checking database connection...")
    
    try:
        # Try to import and test database
        sys.path.insert(0, str(Path(__file__).parent))
        
        from shared.config.phase2_config import config
        from shared.database.models import DatabaseManager
        
        db = DatabaseManager(config.database.url)
        db.create_tables()
        db.close()
        
        print("✅ Database connection successful")
        print(f"✅ Database URL: {config.database.url}")
        return True
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def check_chinese_support():
    """Check Chinese text processing support"""
    print("\n🔍 Checking Chinese support...")
    
    try:
        import jieba
        import opencc
        
        # Test jieba
        test_text = "這是一個股票投資的教學影片"
        words = list(jieba.cut(test_text))
        if "股票" in words and "投資" in words:
            print("✅ jieba tokenization working")
        else:
            print("❌ jieba tokenization issues")
            return False
        
        # Test OpenCC
        cc = opencc.OpenCC('s2t')
        result = cc.convert('股票投资')
        if result:
            print("✅ OpenCC conversion working")
        else:
            print("❌ OpenCC conversion failed")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Chinese support check failed: {e}")
        return False

def check_model_availability():
    """Check if ML models are available"""
    print("\n🔍 Checking ML model availability...")
    
    try:
        from transformers import AutoTokenizer
        
        # Test BERT model download
        tokenizer = AutoTokenizer.from_pretrained("bert-base-chinese")
        if tokenizer:
            print("✅ BERT model available")
        else:
            print("❌ BERT model not available")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Model check failed: {e}")
        print("Note: This is expected on first run - models will be downloaded")
        return True  # Don't fail validation for model downloads

def check_file_permissions():
    """Check file write permissions"""
    print("\n🔍 Checking file permissions...")
    
    try:
        from shared.config.phase2_config import config
        
        # Test write permissions
        test_dirs = [
            Path(config.storage.base_path),
            Path(config.storage.base_path).parent.parent / "phase3_filtering" / "outputs",
            Path(config.logging.file_path).parent
        ]
        
        for test_dir in test_dirs:
            test_dir.mkdir(parents=True, exist_ok=True)
            
            # Test file creation
            test_file = test_dir / "test.txt"
            test_file.write_text("test")
            test_file.unlink()
            
            print(f"✅ {test_dir}")
        
        return True
        
    except Exception as e:
        print(f"❌ File permission check failed: {e}")
        return False

def run_comprehensive_check():
    """Run all validation checks"""
    print("🚀 Phase 2-3 Validation Script")
    print("=" * 50)
    
    checks = [
        ("Python Version", check_python_version),
        ("Dependencies", check_dependencies),
        ("Environment Variables", check_environment_variables),
        ("Filesystem", check_filesystem),
        ("Database Connection", check_database_connection),
        ("Chinese Support", check_chinese_support),
        ("Model Availability", check_model_availability),
        ("File Permissions", check_file_permissions),
    ]
    
    results = []
    for check_name, check_func in checks:
        try:
            result = check_func()
            results.append((check_name, result))
        except Exception as e:
            print(f"❌ {check_name}: Exception - {e}")
            results.append((check_name, False))
    
    print("\n" + "=" * 50)
    print("🎯 Validation Summary")
    print("=" * 50)
    
    passed = 0
    for check_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{check_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n📊 Overall: {passed}/{len(results)} checks passed")
    
    if passed == len(results):
        print("🎉 All checks passed! Phase 2-3 is ready to run.")
        print("\nNext steps:")
        print("1. Run Phase 2: python phase2_indexing/main.py")
        print("2. Run Phase 3: python phase3_filtering/main.py")
        print("3. Or run both: python phase2_indexing/main.py && python phase3_filtering/main.py")
    else:
        print("⚠️  Some checks failed. Please address the issues above.")
        return False
    
    return True

if __name__ == "__main__":
    success = run_comprehensive_check()
    sys.exit(0 if success else 1)
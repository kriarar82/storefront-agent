"""Test script to verify Storefront Agent installation."""

import sys
import importlib
from pathlib import Path


def test_imports():
    """Test that all required modules can be imported."""
    print("🔄 Testing imports...")
    
    # Add src to path
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
    
    required_modules = [
        'storefront_agent.azure_llm_client',
        'storefront_agent.mcp_client', 
        'storefront_agent.storefront_agent',
        'storefront_agent.config',
        'storefront_agent.utils'
    ]
    
    failed_imports = []
    
    for module in required_modules:
        try:
            importlib.import_module(module)
            print(f"✅ {module}")
        except ImportError as e:
            print(f"❌ {module}: {e}")
            failed_imports.append(module)
    
    if failed_imports:
        print(f"\n❌ Failed to import: {', '.join(failed_imports)}")
        return False
    
    print("✅ All imports successful")
    return True


def test_configuration():
    """Test configuration loading."""
    print("\n🔄 Testing configuration...")
    
    try:
        # Test configuration module import
        import storefront_agent.config
        print("✅ Configuration module imported successfully")
        
        # Test configuration classes exist
        from storefront_agent.config import AzureConfig, MCPConfig, AppConfig, StorefrontAgentConfig
        print("✅ Configuration classes found")
        
        # Test that we can create config instances with test values
        test_azure_config = AzureConfig(
            endpoint="https://test.openai.azure.com/",
            api_key="test-key",
            deployment_name="test-deployment"
        )
        print("✅ Azure configuration class works")
        
        test_mcp_config = MCPConfig()
        print("✅ MCP configuration class works")
        
        test_app_config = AppConfig()
        print("✅ App configuration class works")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return False


def test_file_structure():
    """Test that all required files exist."""
    print("\n🔄 Testing file structure...")
    
    required_files = [
        'main.py',
        'src/storefront_agent/storefront_agent.py',
        'src/storefront_agent/azure_llm_client.py',
        'src/storefront_agent/mcp_client.py',
        'src/storefront_agent/config.py',
        'src/storefront_agent/utils.py',
        'requirements.txt',
        'README.md'
    ]
    
    missing_files = []
    
    for file in required_files:
        if Path(file).exists():
            print(f"✅ {file}")
        else:
            print(f"❌ {file}")
            missing_files.append(file)
    
    if missing_files:
        print(f"\n❌ Missing files: {', '.join(missing_files)}")
        return False
    
    print("✅ All required files present")
    return True


def test_dependencies():
    """Test that external dependencies are available."""
    print("\n🔄 Testing dependencies...")
    
    external_deps = [
        'openai',
        'pydantic',
        'loguru',
        'httpx',
        'websockets',
        'aiofiles'
    ]
    
    failed_deps = []
    
    for dep in external_deps:
        try:
            importlib.import_module(dep)
            print(f"✅ {dep}")
        except ImportError:
            print(f"❌ {dep}")
            failed_deps.append(dep)
    
    if failed_deps:
        print(f"\n❌ Missing dependencies: {', '.join(failed_deps)}")
        print("Run: pip install -r requirements.txt")
        return False
    
    print("✅ All dependencies available")
    return True


def main():
    """Run all tests."""
    print("🧪 Storefront Agent Installation Test")
    print("=" * 50)
    
    tests = [
        test_file_structure,
        test_dependencies,
        test_imports,
        test_configuration
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test failed with error: {e}")
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Installation is successful.")
        print("\nNext steps:")
        print("1. Configure your .env file")
        print("2. Run: python main.py")
    else:
        print("❌ Some tests failed. Please check the errors above.")
        sys.exit(1)


if __name__ == "__main__":
    main()

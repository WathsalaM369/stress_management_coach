import inspect

try:
    from agents import stress_estimator
    print("✅ Successfully imported stress_estimator module")
    
    print("\n=== STRESS ESTIMATOR CONTENTS ===")
    for name, obj in inspect.getmembers(stress_estimator):
        if not name.startswith('_'):
            print(f"{name}: {type(obj)}")
    
    print("\n=== AVAILABLE CLASSES ===")
    classes = [name for name, obj in inspect.getmembers(stress_estimator) 
              if inspect.isclass(obj)]
    print(classes)
    
except ImportError as e:
    print(f"❌ Import error: {e}")
except Exception as e:
    print(f"❌ Error: {e}")
#!/usr/bin/env python3
"""
Simple test script for pyresparser integration
"""

def test_pyresparser():
    """Test pyresparser availability"""
    try:
        from pyresparser import ResumeParser
        print("OK - pyresparser imported successfully")
        return True
    except ImportError as e:
        print(f"ERROR - pyresparser import failed: {e}")
        return False

def test_spacy():
    """Test spaCy availability"""
    try:
        import spacy
        nlp = spacy.load("en_core_web_sm")
        print("OK - spaCy model loaded successfully")
        return True
    except Exception as e:
        print(f"ERROR - spaCy failed: {e}")
        return False

def test_nltk():
    """Test NLTK availability"""
    try:
        import nltk
        nltk.data.find('corpora/words')
        print("OK - NLTK words corpus found")
        return True
    except Exception as e:
        print(f"ERROR - NLTK failed: {e}")
        return False

def main():
    print("Testing pyresparser integration...")
    print("=" * 40)
    
    tests = [
        ("pyresparser", test_pyresparser),
        ("spaCy", test_spacy),
        ("NLTK", test_nltk),
    ]
    
    passed = 0
    for name, test_func in tests:
        print(f"\nTesting {name}...")
        if test_func():
            passed += 1
    
    print(f"\nResults: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("SUCCESS - All tests passed! pyresparser is ready to use.")
    else:
        print("FAILED - Some tests failed. Check the error messages above.")

if __name__ == "__main__":
    main()

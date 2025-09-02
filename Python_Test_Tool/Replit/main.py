#!/usr/bin/env python3
"""
Test Automation Framework - Main Entry Point

This tool processes Excel specifications to generate JSON mapping configurations
and creates test files for validation scenarios. It's specifically built for
enterprise data integration testing.

Usage:
    python main.py [option]

Options:
    1. Process Excel specification to JSON
    2. Generate MISS-RE (Missing Required) test files
    3. Generate MISS-OE (Missing Optional) test files
    4. Run all processes
"""

import sys
import os
import subprocess


def print_banner():
    """Print application banner."""
    print("=" * 60)
    print("🔧 TEST AUTOMATION FRAMEWORK")
    print("📋 Data Mapping & Test Generation Tool")
    print("=" * 60)


def print_menu():
    """Print main menu options."""
    print("\n📚 Available Operations:")
    print("1️⃣  Process Excel Specification → JSON Mapping")
    print("2️⃣  Generate MISS-RE Tests (Missing Required Fields)")
    print("3️⃣  Generate MISS-OE Tests (Missing Optional Fields)")
    print("4️⃣  Run All Processes")
    print("5️⃣  Exit")
    print("-" * 40)


def run_excel_processor():
    """Run the Excel to JSON processor."""
    print("\n🔄 Processing Excel specification...")
    try:
        result = subprocess.run(
            [sys.executable, "/Users/mkesharwani/Desktop/Workspace3/maps-automation-framework/Python_Test_Tool/SPEC_TO_JSON/processExcel4.py"],
            capture_output=True,
            text=True,
            cwd=".")

        if result.returncode == 0:
            print("✅ Excel processing completed successfully!")
            print(result.stdout)
        else:
            print("❌ Excel processing failed:")
            print(result.stderr)
            return False
    except Exception as e:
        print(f"❌ Error running Excel processor: {e}")
        return False
    return True


def run_miss_re_generator():
    """Run the MISS-RE test generator."""
    print("\n🔄 Generating MISS-RE tests...")
    try:
        result = subprocess.run(
            [sys.executable, "/Users/mkesharwani/Desktop/Workspace3/maps-automation-framework/Python_Test_Tool/test_generator.py", "required"],
            capture_output=True,
            text=True,
            cwd=".")

        if result.returncode == 0:
            print("✅ MISS-RE test generation completed!")
            print(result.stdout)
        else:
            print("❌ MISS-RE generation failed:")
            print(result.stderr)
            return False
    except Exception as e:
        print(f"❌ Error running MISS-RE generator: {e}")
        return False
    return True


def run_miss_oe_generator():
    """Run the MISS-OE test generator."""
    print("\n🔄 Generating MISS-OE tests...")
    try:
        result = subprocess.run(
            [sys.executable, "/Users/mkesharwani/Desktop/Workspace3/maps-automation-framework/Python_Test_Tool/test_generator.py", "optional"],
            capture_output=True,
            text=True,
            cwd=".")

        if result.returncode == 0:
            print("✅ MISS-OE test generation completed!")
            print(result.stdout)
        else:
            print("❌ MISS-OE generation failed:")
            print(result.stderr)
            return False
    except Exception as e:
        print(f"❌ Error running MISS-OE generator: {e}")
        return False
    return True


def run_all_processes():
    """Run all processes in sequence."""
    print("\n🚀 Running all processes...")

    success = True
    success &= run_excel_processor()

    if success:
        success &= run_miss_re_generator()

    if success:
        success &= run_miss_oe_generator()

    if success:
        print("\n🎉 All processes completed successfully!")
    else:
        print("\n💥 Some processes failed. Check the logs above.")


def main():
    """Main application loop."""
    print_banner()

    # If command line argument provided, run directly
    if len(sys.argv) > 1:
        option = sys.argv[1]
        if option == "1":
            run_excel_processor()
        elif option == "2":
            run_miss_re_generator()
        elif option == "3":
            run_miss_oe_generator()
        elif option == "4":
            run_all_processes()
        else:
            print(f"❌ Unknown option: {option}")
        return

    # Interactive mode
    while True:
        print_menu()
        try:
            choice = input("🔹 Select option (1-5): ").strip()

            if choice == "1":
                run_excel_processor()
            elif choice == "2":
                run_miss_re_generator()
            elif choice == "3":
                run_miss_oe_generator()
            elif choice == "4":
                run_all_processes()
            elif choice == "5":
                print("👋 Goodbye!")
                break
            else:
                print("❌ Invalid choice. Please select 1-5.")

        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()

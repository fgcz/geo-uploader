"""
Simple script to load NCBI taxonomy scientific names
Only loads scientific names for validation purposes
"""

import sys

def load_taxonomy(names_dmp_path):
    return False


def main():
    """Main function with basic argument handling"""

    if len(sys.argv) < 2:
        print("Usage: python load_taxonomy.py <path_to_names.dmp>")
        print("Example: python load_taxonomy.py names.dmp")
        sys.exit(1)

    names_dmp_path = sys.argv[1]

    print("=== NCBI Taxonomy Loader ===")
    print(f"File: {names_dmp_path}")
    print()

    success = load_taxonomy(names_dmp_path)

    if success:
        print("\n🎉 Taxonomy data loaded successfully!")
        print("\nYou can now validate species names in your Flask app using:")
        print("  redis.sismember('taxonomy:scientific_names', species_name)")
        sys.exit(0)
    else:
        print("\n💥 Failed to load taxonomy data")
        sys.exit(1)


if __name__ == "__main__":
    main()
import sys
import os

# Add project root to sys.path if running from a different directory or for complex structures
# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '.'))) # Assuming script is in root

from app.db.base_class import Base
# Importing the models module will execute the table definitions
from app.models import school_class # This will define teacher_class_association

# Access the table from the metadata
tca_table = Base.metadata.tables.get('teacher_class_association')

if tca_table is not None:
    print(f"Table: {tca_table.name}")
    print(f"Primary Key Columns: {[col.name for col in tca_table.primary_key.columns]}")
    # You can also check the constraint name if needed
    for constraint in tca_table.constraints:
        if isinstance(constraint, type(tca_table.primary_key)): # Check if it's a PrimaryKeyConstraint
             print(f"Primary Key Constraint Name (from model): {constraint.name}")
             break
else:
    print("teacher_class_association table not found in metadata.")
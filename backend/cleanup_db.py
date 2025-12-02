"""Script to remove sample/mock products from database."""
import sqlite3

conn = sqlite3.connect('dev.db')
cursor = conn.cursor()

# Find sample products
cursor.execute("SELECT id, title FROM products WHERE title LIKE 'Sample Product%'")
samples = cursor.fetchall()
print(f'Found {len(samples)} sample products to delete:')
for s in samples:
    print(f'  - ID {s[0]}: {s[1]}')

# Delete sample products
cursor.execute("DELETE FROM products WHERE title LIKE 'Sample Product%'")
deleted = cursor.rowcount
conn.commit()
print(f'Deleted {deleted} sample products')

# Delete orphaned chunks
cursor.execute("DELETE FROM product_chunks WHERE product_id NOT IN (SELECT id FROM products)")
deleted_chunks = cursor.rowcount
conn.commit()
print(f'Deleted {deleted_chunks} orphaned chunks')

# Count remaining
cursor.execute('SELECT COUNT(*) FROM products')
remaining = cursor.fetchone()[0]
print(f'Remaining products: {remaining}')

conn.close()
print('Done!')

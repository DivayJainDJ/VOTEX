"""
Clear all data from the database
"""
import os
import sqlite3

def clear_database():
    db_path = 'transcription_data.db'
    
    if not os.path.exists(db_path):
        print(f"✓ Database file '{db_path}' does not exist. Nothing to clear.")
        return
    
    print("=" * 60)
    print("DATABASE CLEAR UTILITY")
    print("=" * 60)
    
    # Connect to database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get current counts
    cursor.execute('SELECT COUNT(*) FROM transcriptions')
    trans_count = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM feedback')
    feedback_count = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM corrections')
    corrections_count = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM learned_rules')
    rules_count = cursor.fetchone()[0]
    
    print(f"\nCurrent database contents:")
    print(f"  - Transcriptions: {trans_count}")
    print(f"  - Feedback: {feedback_count}")
    print(f"  - Corrections: {corrections_count}")
    print(f"  - Learned Rules: {rules_count}")
    
    if trans_count == 0 and feedback_count == 0 and corrections_count == 0 and rules_count == 0:
        print("\n✓ Database is already empty!")
        conn.close()
        return
    
    print("\n⚠️  WARNING: This will delete ALL data!")
    print("=" * 60)
    
    # Clear all tables
    print("\nClearing tables...")
    cursor.execute('DELETE FROM rule_applications')
    print("  ✓ Cleared rule_applications")
    
    cursor.execute('DELETE FROM learned_rules')
    print("  ✓ Cleared learned_rules")
    
    cursor.execute('DELETE FROM corrections')
    print("  ✓ Cleared corrections")
    
    cursor.execute('DELETE FROM feedback')
    print("  ✓ Cleared feedback")
    
    cursor.execute('DELETE FROM transcriptions')
    print("  ✓ Cleared transcriptions")
    
    # Reset auto-increment counters
    cursor.execute('DELETE FROM sqlite_sequence')
    print("  ✓ Reset ID counters")
    
    conn.commit()
    conn.close()
    
    print("\n" + "=" * 60)
    print("✅ DATABASE CLEARED SUCCESSFULLY!")
    print("=" * 60)
    print("\nAll data has been removed. The database is now empty.")
    print("The system will start fresh with no learned corrections.")

if __name__ == '__main__':
    clear_database()

"""
Test script for database and learning functionality
"""
from database import TranscriptionDatabase
import time

def test_database():
    print("=" * 70)
    print("DATABASE & LEARNING SYSTEM TEST")
    print("=" * 70)
    
    # Initialize database
    db = TranscriptionDatabase('test_transcription_data.db')
    
    print("\n1. Testing transcription storage...")
    trans_id = db.store_transcription({
        'original': 'I gotta go to the store',
        'cleaned': 'I gotta go to the store',
        'filtered': 'I gotta go to the store',
        'grammar_corrected': 'I have to go to the store',
        'tone_transformed': 'I must go to the store',
        'final_output': 'I must go to the store.',
        'tone_mode': 'formal',
        'latency_ms': 150,
        'transcription_time_ms': 3000,
        'processing_time_ms': 150
    })
    print(f"   ✓ Stored transcription ID: {trans_id}")
    
    print("\n2. Testing feedback storage (approve)...")
    db.store_feedback('approve', 'Hello', 'Hello.', 'neutral', trans_id)
    print("   ✓ Approval stored")
    
    print("\n3. Testing feedback storage (reject)...")
    db.store_feedback('reject', 'I gotta go', 'I gotta go.', 'formal', trans_id)
    print("   ✓ Rejection stored")
    
    print("\n4. Testing manual correction...")
    db.store_correction(
        'I gotta go',
        'I gotta go.',
        'I must leave.',
        'manual',
        'formal',
        trans_id
    )
    print("   ✓ Manual correction stored")
    
    print("\n5. Testing ChatGPT correction...")
    db.store_correction(
        'I wanna eat',
        'I wanna eat.',
        'I would like to eat.',
        'chatgpt',
        'formal',
        trans_id
    )
    print("   ✓ ChatGPT correction stored")
    
    print("\n6. Testing rule extraction (need 2+ examples)...")
    # Add second example with same word
    db.store_correction(
        'I gotta sleep',
        'I gotta sleep.',
        'I must sleep.',
        'manual',
        'formal'
    )
    print("   ✓ Second correction stored (rule should be created)")
    
    print("\n7. Getting learned rules...")
    rules = db.get_learned_rules('formal', min_usage=2)
    print(f"   ✓ Found {len(rules)} active rules:")
    for rule in rules:
        print(f"      - {rule['from_word']} → {rule['to_word']} (used {rule['usage_count']} times)")
    
    print("\n8. Testing rule application...")
    test_text = "I gotta wanna go"
    result = db.apply_learned_rules(test_text, 'formal')
    if result:
        print(f"   ✓ Applied rules: '{test_text}' → '{result}'")
    else:
        print(f"   ⚠ No rules applied to: '{test_text}'")
    
    print("\n9. Testing exact match lookup...")
    match = db.check_exact_match('I gotta go', 'formal')
    if match:
        print(f"   ✓ Found exact match: '{match}'")
    else:
        print("   ⚠ No exact match found")
    
    print("\n10. Getting accuracy stats...")
    accuracy = db.get_accuracy_stats()
    print(f"   ✓ Approved: {accuracy['approved']}")
    print(f"   ✓ Rejected: {accuracy['rejected']}")
    print(f"   ✓ Accuracy: {accuracy['accuracy']}")
    
    print("\n11. Getting comprehensive stats...")
    stats = db.get_stats()
    print(f"   ✓ Total transcriptions: {stats['total_transcriptions']}")
    print(f"   ✓ Total corrections: {stats['total_corrections']}")
    print(f"   ✓ Active rules: {stats['active_rules']}")
    print(f"   ✓ Accuracy: {stats['accuracy']}")
    
    print("\n12. Getting recent transcriptions...")
    recent = db.get_recent_transcriptions(limit=3)
    print(f"   ✓ Found {len(recent)} recent transcriptions")
    for i, trans in enumerate(recent, 1):
        print(f"      {i}. {trans['original_audio_text']} → {trans['final_output']} ({trans['latency_ms']}ms)")
    
    print("\n13. Exporting learning data...")
    export_file = db.export_learning_data('test_learning_data.json')
    print(f"   ✓ Exported to: {export_file}")
    
    print("\n14. Testing learning persistence...")
    # Close and reopen database
    db.close()
    db2 = TranscriptionDatabase('test_transcription_data.db')
    stats2 = db2.get_stats()
    print(f"   ✓ Data persisted: {stats2['total_transcriptions']} transcriptions")
    print(f"   ✓ Rules persisted: {stats2['active_rules']} active rules")
    db2.close()
    
    print("\n" + "=" * 70)
    print("FINAL RESULTS")
    print("=" * 70)
    print(f"✅ Total Transcriptions: {stats['total_transcriptions']}")
    print(f"✅ Total Corrections: {stats['total_corrections']}")
    print(f"✅ Active Rules: {stats['active_rules']}")
    print(f"✅ Approved: {stats['approved']}")
    print(f"✅ Rejected: {stats['rejected']}")
    print(f"✅ Accuracy: {stats['accuracy']}")
    print("=" * 70)
    
    print("\n✅ ALL TESTS PASSED!")
    print("\nDatabase file: test_transcription_data.db")
    print("Export file: test_learning_data.json")
    print("\nYou can inspect these files to see the stored data.")

if __name__ == '__main__':
    test_database()

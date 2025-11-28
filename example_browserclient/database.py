"""
SQLite Database for storing transcriptions, feedback, and learning data
"""
import sqlite3
import json
from datetime import datetime
from pathlib import Path


class TranscriptionDatabase:
    def __init__(self, db_path='transcription_data.db'):
        self.db_path = db_path
        self.conn = None
        self.init_database()
    
    def init_database(self):
        """Initialize database with all required tables"""
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row  # Return rows as dictionaries
        
        cursor = self.conn.cursor()
        
        # Table 1: Transcriptions
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transcriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                original_audio_text TEXT NOT NULL,
                cleaned_text TEXT,
                filtered_text TEXT,
                grammar_corrected TEXT,
                tone_transformed TEXT,
                final_output TEXT NOT NULL,
                tone_mode TEXT NOT NULL,
                latency_ms INTEGER,
                transcription_time_ms INTEGER,
                processing_time_ms INTEGER
            )
        ''')
        
        # Table 2: Feedback (Approvals/Rejections)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                transcription_id INTEGER,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                feedback_type TEXT NOT NULL,  -- 'approve' or 'reject'
                original_text TEXT NOT NULL,
                output_text TEXT NOT NULL,
                tone_mode TEXT NOT NULL,
                FOREIGN KEY (transcription_id) REFERENCES transcriptions(id)
            )
        ''')
        
        # Table 3: Corrections (Manual and Auto)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS corrections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                transcription_id INTEGER,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                original_text TEXT NOT NULL,
                wrong_output TEXT NOT NULL,
                corrected_output TEXT NOT NULL,
                correction_type TEXT NOT NULL,  -- 'manual' or 'chatgpt'
                tone_mode TEXT NOT NULL,
                FOREIGN KEY (transcription_id) REFERENCES transcriptions(id)
            )
        ''')
        
        # Table 4: Learned Rules
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS learned_rules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rule_key TEXT UNIQUE NOT NULL,
                from_word TEXT NOT NULL,
                to_word TEXT NOT NULL,
                tone_mode TEXT NOT NULL,
                usage_count INTEGER DEFAULT 1,
                success_count INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_used DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Table 5: Rule Applications (Track when rules are used)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS rule_applications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rule_id INTEGER NOT NULL,
                transcription_id INTEGER,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                was_successful BOOLEAN DEFAULT 1,
                FOREIGN KEY (rule_id) REFERENCES learned_rules(id),
                FOREIGN KEY (transcription_id) REFERENCES transcriptions(id)
            )
        ''')
        
        self.conn.commit()
        print("✓ Database initialized successfully")
    
    def store_transcription(self, data):
        """Store a complete transcription with all processing stages"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO transcriptions (
                original_audio_text, cleaned_text, filtered_text,
                grammar_corrected, tone_transformed, final_output,
                tone_mode, latency_ms, transcription_time_ms, processing_time_ms
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data.get('original'),
            data.get('cleaned'),
            data.get('filtered'),
            data.get('grammar_corrected'),
            data.get('tone_transformed'),
            data.get('final_output'),
            data.get('tone_mode'),
            data.get('latency_ms'),
            data.get('transcription_time_ms'),
            data.get('processing_time_ms')
        ))
        self.conn.commit()
        return cursor.lastrowid
    
    def store_feedback(self, feedback_type, original, output, tone_mode, transcription_id=None):
        """Store user feedback (approve/reject)"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO feedback (transcription_id, feedback_type, original_text, output_text, tone_mode)
            VALUES (?, ?, ?, ?, ?)
        ''', (transcription_id, feedback_type, original, output, tone_mode))
        self.conn.commit()
        return cursor.lastrowid
    
    def store_correction(self, original, wrong_output, corrected_output, correction_type, tone_mode, transcription_id=None):
        """Store a correction (manual or ChatGPT)"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO corrections (
                transcription_id, original_text, wrong_output, 
                corrected_output, correction_type, tone_mode
            ) VALUES (?, ?, ?, ?, ?, ?)
        ''', (transcription_id, original, wrong_output, corrected_output, correction_type, tone_mode))
        self.conn.commit()
        
        # Extract and store learned rules
        self._extract_and_store_rules(original, corrected_output, tone_mode)
        
        return cursor.lastrowid
    
    def _extract_and_store_rules(self, original, corrected, tone_mode):
        """Extract word-level rules and store them"""
        original_words = original.lower().split()
        corrected_words = corrected.lower().split()
        
        cursor = self.conn.cursor()
        
        for i, word in enumerate(original_words):
            if i < len(corrected_words) and word != corrected_words[i]:
                rule_key = f"{word}→{corrected_words[i]}:{tone_mode}"
                
                # Check if rule exists
                cursor.execute('SELECT id, usage_count FROM learned_rules WHERE rule_key = ?', (rule_key,))
                existing = cursor.fetchone()
                
                if existing:
                    # Update existing rule
                    cursor.execute('''
                        UPDATE learned_rules 
                        SET usage_count = usage_count + 1, last_used = CURRENT_TIMESTAMP
                        WHERE id = ?
                    ''', (existing['id'],))
                else:
                    # Create new rule
                    cursor.execute('''
                        INSERT INTO learned_rules (rule_key, from_word, to_word, tone_mode)
                        VALUES (?, ?, ?, ?)
                    ''', (rule_key, word, corrected_words[i], tone_mode))
        
        self.conn.commit()
    
    def get_learned_rules(self, tone_mode, min_usage=2):
        """Get active learned rules for a tone mode"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM learned_rules 
            WHERE tone_mode = ? AND usage_count >= ?
            ORDER BY usage_count DESC
        ''', (tone_mode, min_usage))
        return cursor.fetchall()
    
    def apply_learned_rules(self, text, tone_mode):
        """Apply learned rules to text"""
        rules = self.get_learned_rules(tone_mode)
        result = text
        
        for rule in rules:
            result = result.replace(rule['from_word'], rule['to_word'])
        
        return result if result != text else None
    
    def check_exact_match(self, original, tone_mode):
        """Check if we have an exact correction for this input"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT corrected_output, COUNT(*) as count
            FROM corrections
            WHERE LOWER(original_text) = LOWER(?) AND tone_mode = ?
            GROUP BY corrected_output
            ORDER BY count DESC
            LIMIT 1
        ''', (original, tone_mode))
        result = cursor.fetchone()
        return result['corrected_output'] if result else None
    
    def get_accuracy_stats(self):
        """Calculate accuracy based on approvals vs rejections"""
        cursor = self.conn.cursor()
        
        cursor.execute('SELECT COUNT(*) as count FROM feedback WHERE feedback_type = "approve"')
        approved = cursor.fetchone()['count']
        
        cursor.execute('SELECT COUNT(*) as count FROM feedback WHERE feedback_type = "reject"')
        rejected = cursor.fetchone()['count']
        
        total = approved + rejected
        accuracy = (approved / total * 100) if total > 0 else 0
        
        return {
            'approved': approved,
            'rejected': rejected,
            'total': total,
            'accuracy': f"{accuracy:.1f}%"
        }
    
    def get_stats(self):
        """Get comprehensive statistics"""
        cursor = self.conn.cursor()
        
        cursor.execute('SELECT COUNT(*) as count FROM transcriptions')
        total_transcriptions = cursor.fetchone()['count']
        
        cursor.execute('SELECT COUNT(*) as count FROM corrections')
        total_corrections = cursor.fetchone()['count']
        
        cursor.execute('SELECT COUNT(*) as count FROM learned_rules WHERE usage_count >= 2')
        active_rules = cursor.fetchone()['count']
        
        accuracy_stats = self.get_accuracy_stats()
        
        return {
            'total_transcriptions': total_transcriptions,
            'total_corrections': total_corrections,
            'active_rules': active_rules,
            **accuracy_stats
        }
    
    def get_recent_transcriptions(self, limit=10):
        """Get recent transcriptions"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM transcriptions 
            ORDER BY timestamp DESC 
            LIMIT ?
        ''', (limit,))
        return cursor.fetchall()
    
    def export_learning_data(self, output_file='learning_data.json'):
        """Export all learning data to JSON"""
        cursor = self.conn.cursor()
        
        # Get all corrections
        cursor.execute('SELECT * FROM corrections ORDER BY timestamp')
        corrections = [dict(row) for row in cursor.fetchall()]
        
        # Get all rules
        cursor.execute('SELECT * FROM learned_rules ORDER BY usage_count DESC')
        rules = [dict(row) for row in cursor.fetchall()]
        
        # Get feedback stats
        stats = self.get_stats()
        
        data = {
            'exported_at': datetime.now().isoformat(),
            'stats': stats,
            'corrections': corrections,
            'learned_rules': rules
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"✓ Learning data exported to {output_file}")
        return output_file
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()

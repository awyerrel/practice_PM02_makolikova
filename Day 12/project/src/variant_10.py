import csv
import json
import os
import time
import tracemalloc
from typing import List, Dict, Any, Optional

#  CONSTANTS 
CACHE_MAX_SIZE = 1000
results_cache = []


#  MAIN CLASS 
class FileProcessor:
    """
    Class for processing file data
    Contains methods for loading, processing and saving data
    """
    
    def __init__(self, filename: str):
        """
        Initialize processor
        
        Args:
            filename: path to CSV file with data
        """
        self.filename = filename
        self.data = []
        self.processed_count = 0
        
    def load_data(self) -> None:
        """
        Load data from CSV file
        Fixed version with error handling
        """
        print(f"Loading data from {self.filename}")
        
        try:
            # CHECK 1: File existence
            if not os.path.exists(self.filename):
                raise FileNotFoundError(f"File '{self.filename}' not found")
            
            # CHECK 2: File not empty
            if os.path.getsize(self.filename) == 0:
                raise ValueError(f"File '{self.filename}' is empty")
            
            # Load data using DictReader
            with open(self.filename, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                
                # Check for headers
                if not reader.fieldnames:
                    raise ValueError("CSV file has no headers")
                
                # Expected columns
                expected_columns = ['Name', 'Age', 'Score']
                for col in expected_columns:
                    if col not in reader.fieldnames:
                        raise ValueError(f"CSV missing column '{col}'")
                
                # Read data
                for row_num, row in enumerate(reader, start=2):
                    try:
                        # CHECK 3: Data validation
                        name = row['Name'].strip()
                        if not name:
                            print(f"Warning: row {row_num} has empty name, skipping")
                            continue
                        
                        age = int(row['Age'])
                        if age < 0:
                            print(f"Warning: row {row_num} has negative age ({age}), skipping")
                            continue
                        
                        score = float(row['Score'])
                        if score < 0 or score > 100:
                            print(f"Warning: row {row_num} has invalid score ({score}), skipping")
                            continue
                        
                        self.data.append({
                            'name': name,
                            'age': age,
                            'score': score
                        })
                        
                    except ValueError as e:
                        print(f"Warning: row {row_num} conversion error - {e}")
                        continue
            
            print(f"Loaded {len(self.data)} records")
            
        except Exception as e:
            print(f"Critical loading error: {e}")
            raise
    
    def process_data(self) -> None:
        """
        Process data with error protection
        Fixed version with guard clauses
        """
        print(f"Processing {len(self.data)} records...")
        
        for idx, item in enumerate(self.data):
            print(f"  Processing #{idx+1}: {item['name']}", end=" ")
            
            #  CHECK 4: Division by zero protection 
            if item['age'] == 0:
                print(f"Warning: age = 0, skipping")
                continue
            
            #  FIX 1: Correct bonus formula 
            if item['age'] > 18:
                bonus = item['score'] * 1.15
            else:
                bonus = item['score'] * 0.9
            
            #  FIX 2: Safe division 
            if item['age'] > 0:
                ratio = item['score'] / item['age']
            else:
                ratio = 0
            
            #  FIX 3: Cache size limit 
            if len(results_cache) >= CACHE_MAX_SIZE:
                removed = results_cache.pop(0)
                print(f"(removed old cache for {removed['name']})", end=" ")
            
            # Save to cache
            result_entry = {
                'name': item['name'],
                'age': item['age'],
                'score': item['score'],
                'bonus': round(bonus, 2),
                'ratio': round(ratio, 2),
                'timestamp': time.time()
            }
            results_cache.append(result_entry)
            self.processed_count += 1
            
            #  FIX 4: Safe temporary file writing 
            temp_filename = f"temp_{item['name']}.tmp"
            try:
                with open(temp_filename, 'w', encoding='utf-8') as temp_file:
                    temp_file.write(f"{item['name']},{bonus:.2f},{ratio:.2f}\n")
                print(f"OK (bonus={bonus:.2f}, ratio={ratio:.2f})")
            except Exception as e:
                print(f"Error writing temp file: {e}")
    
    def save_results(self, output_file: str) -> None:
        """
        Save results to JSON file
        
        Args:
            output_file: path to output JSON file
        """
        print(f"Saving results to {output_file}")
        
        try:
            # Create directory if needed
            dirname = os.path.dirname(output_file)
            if dirname:
                os.makedirs(dirname, exist_ok=True)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'total_processed': self.processed_count,
                    'results': results_cache,
                    'timestamp': time.time()
                }, f, indent=2, ensure_ascii=False)
            
            print(f"Results saved ({self.processed_count} records)")
            
        except Exception as e:
            print(f"Error saving: {e}")
            raise
    
    def calculate_statistics(self) -> Dict[str, Any]:
        """
        Calculate statistics from data
        
        Returns:
            Dict with statistics
        """
        print("Calculating statistics...")
        
        if not self.data:
            print("No data for statistics")
            return {
                'count': 0,
                'avg_score': 0.0,
                'min_score': 0.0,
                'max_score': 0.0,
                'avg_age': 0.0
            }
        
        scores = [item['score'] for item in self.data]
        ages = [item['age'] for item in self.data]
        
        stats = {
            'count': len(self.data),
            'avg_score': round(sum(scores) / len(scores), 2),
            'min_score': min(scores),
            'max_score': max(scores),
            'avg_age': round(sum(ages) / len(ages), 2)
        }
        
        print(f"  Average score: {stats['avg_score']}")
        print(f"  Average age: {stats['avg_age']}")
        
        return stats
    
    def recursive_scan(self, path: str, max_depth: int = 3, current_depth: int = 0) -> None:
        """
        Recursive file scan with depth limit
        
        Args:
            path: path to scan
            max_depth: maximum recursion depth
            current_depth: current depth (internal parameter)
        """
        if current_depth >= max_depth:
            print(f"{'  ' * current_depth}Max depth reached ({max_depth})")
            return
        
        try:
            entries = os.listdir(path)
            print(f"{'  ' * current_depth}Scanning: {path}")
            
            for entry in entries:
                full_path = os.path.join(path, entry)
                
                # Skip system files
                if entry.startswith('.'):
                    continue
                
                if os.path.isdir(full_path):
                    self.recursive_scan(full_path, max_depth, current_depth + 1)
                else:
                    try:
                        #  FIX 5: Context manager 
                        with open(full_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            size = len(content)
                            print(f"{'  ' * (current_depth + 1)}File: {entry} - {size} bytes")
                    except Exception as e:
                        print(f"{'  ' * (current_depth + 1)}Error reading {entry}: {e}")
                        
        except PermissionError:
            print(f"{'  ' * current_depth}Permission denied for {path}")
        except Exception as e:
            print(f"{'  ' * current_depth}Error scanning {path}: {e}")


#  HELPER FUNCTIONS 
def create_test_data() -> str:
    """
    Create test CSV file with data
    
    Returns:
        str: path to created file
    """
    print("Creating test data...")
    
    # Check if file exists
    if os.path.exists('test_data.csv'):
        print("  File test_data.csv already exists")
        return "test_data.csv"
    
    # Test data
    test_data = [
        ['Name', 'Age', 'Score'],
        ['Alice', '25', '85.5'],
        ['Bob', '17', '72.0'],
        ['Charlie', '0', '90.0'],
        ['David', '30', '95.5'],
        ['Eve', '22', '88.5'],
        ['Frank', '19', '76.0'],
        ['Grace', '16', '82.5'],
        ['Henry', '24', '91.0'],
        ['Ivy', '0', '78.0'],
        ['Jack', '21', '84.0'],
    ]
    
    try:
        with open('test_data.csv', 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerows(test_data)
        print(f"  Created test file test_data.csv ({len(test_data)-1} records)")
    except Exception as e:
        print(f"  Error creating test file: {e}")
        raise
    
    return "test_data.csv"


def print_memory_stats() -> None:
    """Print memory usage statistics"""
    snapshot = tracemalloc.take_snapshot()
    top_stats = snapshot.statistics('lineno')
    
    print("\nMEMORY STATISTICS:")
    print("-" * 60)
    print(f"  Total allocated: {sum(stat.size for stat in top_stats) / 1024:.2f} KB")
    print(f"  Total objects: {sum(stat.count for stat in top_stats)}")
    print("\n  Top 5 by usage:")
    
    for i, stat in enumerate(top_stats[:5], 1):
        frame = stat.traceback[0]
        filename = frame.filename
        lineno = frame.lineno
        print(f"    {i}. {filename}:{lineno}")
        print(f"       Size: {stat.size / 1024:.2f} KB, Count: {stat.count}")
    
    print("-" * 60)


#  MAIN FUNCTION 
def main() -> None:
    """
    Main function
    """
    print("\n" + "="*60)
    print("  PROGRAM DEBUGGING - VARIANT No. 10")
    print("  File Data Processing")
    print("="*60 + "\n")
    
    #  START MEMORY TRACING 
    tracemalloc.start()
    
    try:
        #  STEP 1: Create test data 
        filename = create_test_data()
        
        #  STEP 2: Initialize processor 
        processor = FileProcessor(filename)
        
        #  STEP 3: Load data 
        processor.load_data()
        
        #  STEP 4: Process data 
        processor.process_data()
        
        #  STEP 5: Calculate statistics 
        stats = processor.calculate_statistics()
        
        #  STEP 6: Save results 
        processor.save_results('results.json')
        
        #  STEP 7: Recursive scan (optional) 
        print("\nRecursive scanning current directory:")
        print("-" * 60)
        processor.recursive_scan('.', max_depth=2)
        print("-" * 60)
        
        #  STEP 8: Memory statistics 
        print_memory_stats()
        
        #  STEP 9: Summary 
        print("\n" + "="*60)
        print("  PROGRAM COMPLETED SUCCESSFULLY")
        print(f"  Processed records: {processor.processed_count}")
        print(f"  Cache size: {len(results_cache)}")
        print("="*60 + "\n")
        
    except Exception as e:
        print("\n" + "="*60)
        print("  CRITICAL ERROR")
        print("="*60)
        print(f"\nError: {e}")
        
        import traceback
        print("\nFull traceback:")
        traceback.print_exc()
        
        print("\n" + "="*60)
        return 1
    
    return 0


#  ENTRY POINT 
if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)
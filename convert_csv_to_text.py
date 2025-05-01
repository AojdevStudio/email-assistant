import csv

def convert_csv_to_text():
    input_file = "dental_kpi_metrics.csv"
    output_file = "dental_kpi_metrics.txt"
    
    print(f"Converting {input_file} to {output_file}...")
    
    with open(input_file, 'r', encoding='utf-8') as infile:
        # Read CSV
        reader = csv.reader(infile)
        rows = [row for row in reader]
        
        # Clean up whitespace
        rows = [[col.strip() for col in row] for row in rows]
        
        with open(output_file, 'w', encoding='utf-8') as outfile:
            outfile.write("Dental Practice KPI Metrics and Benchmarks\n")
            outfile.write("=====================================\n\n")
            
            # Skip header row when writing
            for row in rows[1:]:
                kpi, formula, low, target, stretch = row
                
                # Write each KPI as a section
                outfile.write(f"KPI: {kpi}\n")
                outfile.write("-" * (len(kpi) + 5) + "\n")
                outfile.write(f"Formula: {formula}\n")
                outfile.write("\nBenchmarks:\n")
                outfile.write(f"- Low: {low}\n")
                outfile.write(f"- Target: {target}\n")
                outfile.write(f"- Stretch: {stretch}\n")
                outfile.write("\n---\n\n")
    
    print("Conversion complete!")

if __name__ == "__main__":
    convert_csv_to_text() 
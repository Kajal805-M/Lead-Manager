def parse_csv_test():
    test_csv = '''name,location,requirement,budget,timeline,message
Vikram Singhania,Whitefield,3BHK ready to move,1.6 Cr,Within 1 month,"Looking for ready to move 3BHK flat near ITPL. Loan sanctioned from HDFC, immediate registration."
Ananya Sharma,Sarjapur Road,2BHK,85 L,2-3 months,"Need a 2BHK in gated community near Sarjapur Road with good amenities for children."
Karan Patel,Hebbal,4BHK Luxury Penthouse,3.5 Cr,1-2 months,"Looking for high-floor luxury penthouse with panoramic lake view."'''
    lines = test_csv.strip().splitlines()
    print(f"Header: {lines[0]}")
    print(f"Data lines: {len(lines) - 1}")

parse_csv_test()

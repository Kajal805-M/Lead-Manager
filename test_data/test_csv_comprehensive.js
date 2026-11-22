// Comprehensive CSV Workflow Verification Suite (Client & Parsing)
const fs = require('fs');
const path = require('path');

// Extract the CSV parser functions from mockup/app.js
const appJsPath = path.join(__dirname, '..', 'mockup', 'app.js');
const appJsContent = fs.readFileSync(appJsPath, 'utf8');

// Isolate functions for isolated headless testing
const vm = require('vm');
const sandbox = {
  console: console,
  leads: [
    { id: "L01", name: "Aman Verma", phone: "+91 98765 43210", location: "Whitefield", priority: "Hot", score: 92 },
    { id: "L02", name: "Priya Nair", phone: "+91 98111 22334", location: "Sarjapur Road", priority: "Warm", score: 68 }
  ]
};

// Extract functions
const fnRegex = /(function parseCSVLine[\s\S]*?)(?=\/\/ Helper functions)/;
const match = appJsContent.match(fnRegex);

if (!match) {
  console.error("FAIL: Could not locate parseCSVLine / parseCSVText in app.js");
  process.exit(1);
}

// Also grab normalizePhoneNumber
const normRegex = /(function normalizePhoneNumber[\s\S]*?)(?=\nfunction createEvaluatedLead)/;
const normMatch = appJsContent.match(normRegex);

const codeToRun = `
${normMatch ? normMatch[1] : ''}
${match[1]}
`;

vm.createContext(sandbox);
vm.runInContext(codeToRun, sandbox);

const { parseCSVText, parseCSVLine } = sandbox;

console.log("=================================================");
console.log("RUNNING COMPREHENSIVE CSV CLIENT VERIFICATION");
console.log("=================================================\n");

let passedTests = 0;
let failedTests = 0;

function assert(condition, testName) {
  if (condition) {
    console.log(`  [PASS] ${testName}`);
    passedTests++;
  } else {
    console.error(`  [FAIL] ${testName}`);
    failedTests++;
  }
}

// TEST 1: Standard Benchmark CSV
const csv1 = `name,phone,location,requirement,budget,timeline,message
Vikram Singhania,+91 98765 43210,Whitefield,3BHK ready to move,1.6 Cr,Within 1 month,"Looking for ready to move 3BHK flat near ITPL. Loan sanctioned from HDFC, immediate registration."
Ananya Sharma,+91 98111 22334,Sarjapur Road,2BHK,85 L,2-3 months,"Need a 2BHK in gated community near Sarjapur Road with good amenities for children."`;

const res1 = parseCSVText(csv1);
assert(res1.length === 2, "Test 1: Parses 2 standard rows correctly");
assert(res1[0].name === "Vikram Singhania", "Test 1: First name mapped accurately");
assert(res1[0].phone === "+91 98765 43210", "Test 1: Phone mapped accurately");
assert(res1[0].budget === "1.6 Cr", "Test 1: Budget mapped accurately");

// TEST 2: Escaped quotes and commas within quotes
const csv2 = `name,phone,location,requirement,budget,timeline,message
"Patel, Karan",+91 99000 88776,Hebbal,"4BHK, Luxury Penthouse",3.5 Cr,1-2 months,"Looking for lake view, 2 covered car parks, and ""A-Khata"" approval."`;

const res2 = parseCSVText(csv2);
assert(res2.length === 1, "Test 2: Handles comma inside quoted name and requirement");
assert(res2[0].name === "Patel, Karan", "Test 2: Quoted name with comma preserved");
assert(res2[0].requirement === "4BHK, Luxury Penthouse", "Test 2: Quoted requirement with comma preserved");
assert(res2[0].message.includes('"A-Khata"'), "Test 2: Escaped double-quotes properly unescaped to single double-quote");

// TEST 3: Multiline Quoted Messages (RFC 4180)
const csv3 = `name,phone,location,requirement,budget,timeline,message
Rohan Gupta,+91 99887 76655,Indiranagar,3BHK,2.8 Cr,Immediate,"Line 1: High floor required.
Line 2: 2 covered parking slots needed.
Line 3: Immediate registration."`;

const res3 = parseCSVText(csv3);
assert(res3.length === 1, "Test 3: Multiline quoted field parsed as single record");
assert(res3[0].message.includes("Line 1:") && res3[0].message.includes("Line 3:"), "Test 3: Internal newlines preserved in message field");

// TEST 4: UTF-8 BOM Stripping (Excel Windows export)
const csv4 = "\uFEFFname,phone,location,requirement,budget,timeline,message\r\nSuresh Raina,+91 91234 56789,Whitefield,3BHK,1.5 Cr,Within 1 month,Inbound lead";
const res4 = parseCSVText(csv4);
assert(res4.length === 1, "Test 4: BOM stripped cleanly");
assert(res4[0].name === "Suresh Raina", "Test 4: First column header not corrupted by BOM");

// TEST 5: Alternate Semicolon Delimiter (European Excel format)
const csv5 = `name;phone;location;requirement;budget;timeline;message
Meera Sen;+91 98765 12345;Koramangala;2BHK;1.1 Cr;2 months;Looking for peaceful locality`;
const res5 = parseCSVText(csv5);
assert(res5.length === 1, "Test 5: Auto-detects semicolon delimiter");
assert(res5[0].location === "Koramangala", "Test 5: Semicolon fields properly partitioned");

// TEST 6: Flexible Column Headers (aliases)
const csv6 = `Customer Name,Contact Number,Area,Property Type,Price / Budget,When Needed,Inquiry Notes
Aditya Roy,9876500000,Bannerghatta,Villa,2.5 Cr,Immediate,Looking for independent duplex villa`;
const res6 = parseCSVText(csv6);
assert(res6.length === 1, "Test 6: Maps aliases (Customer Name, Contact Number, Area, Property Type, When Needed, Notes)");
assert(res6[0].name === "Aditya Roy", "Test 6: Customer Name alias mapped to name");
assert(res6[0].location === "Bannerghatta", "Test 6: Area alias mapped to location");
assert(res6[0].requirement === "Villa", "Test 6: Property Type alias mapped to requirement");

// TEST 7: Duplicate Records Detection
// We have sandbox.leads with "Aman Verma" and "+91 98765 43210"
const csv7 = `name,phone,location,requirement,budget,timeline,message
Aman Verma,+91 98765 43210,Whitefield,3BHK,1.5 Cr,Within 1 month,Duplicate of existing lead
New Person,+91 99999 88888,Whitefield,2BHK,90 L,1 month,Brand new lead
New Person,+91 99999 88888,Whitefield,2BHK,90 L,1 month,Duplicate of row 2 within this CSV`;
const res7 = parseCSVText(csv7);
assert(res7.length === 3, "Test 7: All 3 rows processed");
assert(res7[0].is_duplicate === true && res7[0].duplicate_reason.includes("CRM"), "Test 7: Row 1 flagged as duplicate against CRM database");
assert(res7[1].is_duplicate === false, "Test 7: Row 2 flagged as valid new lead");
assert(res7[2].is_duplicate === true && res7[2].duplicate_reason.includes("CSV"), "Test 7: Row 3 flagged as duplicate within CSV");

// TEST 8: Missing Values & Empty Lines
const csv8 = `name,phone,location,requirement,budget,timeline,message
Deepak Kumar,,Whitefield,3BHK,1.2 Cr,,Interested in site visit
,,,,,,
, , , , , , 

Shreya Ghoshal,+91 98222 33445,,2BHK,80 L,1 month,Inquiry`;
const res8 = parseCSVText(csv8);
assert(res8.length === 2, "Test 8: Completely empty and whitespace-only rows are discarded");
assert(res8[0].name === "Deepak Kumar", "Test 8: First valid lead parsed");
assert(res8[0].timeline === "Within 1 month", "Test 8: Missing timeline defaults cleanly");
assert(res8[1].location === "Bangalore", "Test 8: Missing location defaults to Bangalore");

console.log(`\nClient CSV Tests Finished: ${passedTests} Passed, ${failedTests} Failed.`);
if (failedTests > 0) process.exit(1);

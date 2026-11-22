
// -------------------------------------------------------------
// Follow-Up Hub AI Chat System (English + Hinglish)
// -------------------------------------------------------------
let hubChatMessages = [
  {
    sender: "assistant",
    text: "Hello! I am your **Follow-Up AI Assistant**. Ask me anything about today's follow-up priorities, scheduling cadences, drafting WhatsApp messages, or overcoming stalled deals in English or Hinglish!"
  }
];

function renderHubChatThread() {
  const container = document.getElementById("hubChatThread");
  if (!container) return;
  container.innerHTML = "";

  hubChatMessages.forEach(msg => {
    const bubble = document.createElement("div");
    bubble.className = `chat-msg ${msg.sender}`;
    const senderName = msg.sender === "user" ? "SALES AGENT" : "FOLLOW-UP COPILOT";
    const formattedText = msg.text
      .replace(/\n/g, "<br>")
      .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
      .replace(/\*(.*?)\*/g, "<em>$1</em>");

    bubble.innerHTML = `
      <div class="chat-sender">${senderName}</div>
      <div class="chat-bubble">${formattedText}</div>
    `;
    container.appendChild(bubble);
  });

  container.scrollTop = container.scrollHeight;
}

function generateHubAssistantReply(query) {
  const q = query.toLowerCase();
  const isHinglish = isHinglishQuery(query);
  const dueLeads = leads.filter(l => l.followup && l.followup.status === "due");

  // --- HINGLISH REPLIES ---
  if (isHinglish) {
    if (q.includes("aaj") || q.includes("due") || q.includes("kisko") || q.includes("kaun") || q.includes("lead")) {
      const topDue = dueLeads.slice(0, 4);
      let listStr = topDue.map(l => {
        const goalText = (l.followup && l.followup.goal) || "Follow-up";
        return `• **${l.name}** (${l.priority}): ${goalText}`;
      }).join("\n");
      return `Aaj total **${dueLeads.length} leads** due hain:\n\n${listStr || '• Koi lead pending nahi hai.'}\n\n• **Action**: Pehle Hot leads ko call karke site visit fix karein.`;
    }

    if (q.includes("warm") || q.includes("nurture") || q.includes("pushy")) {
      return `**Warm Leads (48-72h Cadence):**\n\n` +
             `• **Value Share**: Brochure ya video walkthrough bhejein, direct "kab kharid rahe ho" na poochein.\n` +
             `• **Consultative**: "Aapke budget mein matching unit aayi hai" keh kar call karein.\n` +
             `• **Soft Close**: Weekend par short 15-minute visit offer karein.`;
    }

    if (q.includes("cold") || q.includes("stalled") || q.includes("inactive")) {
      return `**Cold Lead Re-engagement:**\n\n` +
             `*"Namaste [Name], aapke selected area mein nayi inventory release hui hai. Kya main 1-page summary WhatsApp par share kar doon?"*\n\n` +
             `• Value-led approach se buyer bina pressure ke reply karta hai.`;
    }

    return `**Follow-Up Cadence Rules:**\n\n` +
           `• **Hot Leads**: 24h ke andar call (Goal: Site visit)\n` +
           `• **Warm Leads**: Har 48-72h mein consultative touchpoint\n` +
           `• **Cold Leads**: 14-30 din automated market updates`;
  }

  // --- ENGLISH REPLIES ---
  if (q.includes("due") || q.includes("today") || q.includes("which") || q.includes("hot")) {
    const topDue = dueLeads.slice(0, 4);
    let listStr = topDue.map(l => {
      const goalText = (l.followup && l.followup.goal) || "Follow-up";
      return `• **${l.name}** (${l.priority}): ${goalText}`;
    }).join("\n");
    return `**${dueLeads.length} follow-up actions due today**:\n\n${listStr || '• No pending leads.'}\n\n• **Priority**: Complete Hot lead calls before afternoon window.`;
  }

  if (q.includes("warm") || q.includes("pushy") || q.includes("strategy")) {
    return `**Warm Follow-Up Strategy (48-72h Cadence):**\n\n` +
           `• **Lead with value**: Share floor plans or bank pre-approval options.\n` +
           `• **Consultative angle**: "Checking in with new inventory matching your criteria."\n` +
           `• **Soft CTA**: Propose an informal 15-minute weekend walkthrough.`;
  }

  if (q.includes("cold") || q.includes("re-engage") || q.includes("draft") || q.includes("message")) {
    return `**Cold Lead Re-engagement Message:**\n\n` +
           `*"Hi [Name], new verified inventory just opened up in your preferred area matching your budget. Would you like a quick 1-page summary on WhatsApp?"*\n\n` +
           `• Non-pushy, opens dialogue with zero sales friction.`;
  }

  return `**Follow-Up Cadence Summary:**\n\n` +
         `• **Hot (≥70)**: Daily contact (≤24h) to confirm site visits.\n` +
         `• **Warm (40-69)**: Consultative check-ins every 48-72h.\n` +
         `• **Cold (<40)**: 14-30 day nurture with market price updates.`;
}

function setupHubChat() {
  const form = document.getElementById("hubChatForm");
  const input = document.getElementById("hubChatInput");

  if (form && input) {
    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      const q = input.value.trim();
      if (!q) return;

      hubChatMessages.push({ sender: "user", text: q });
      renderHubChatThread();
      input.value = "";

      // Try calling live Flask API
      try {
        const res = await fetch("/api/followup/chat", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ query: q })
        });
        if (res.ok) {
          const data = await res.json();
          if (data.success && data.reply) {
            hubChatMessages.push({ sender: "assistant", text: data.reply });
            renderHubChatThread();
            return;
          }
        }
      } catch (err) {
        // Offline / fallback mode
      }

      setTimeout(() => {
        const reply = generateHubAssistantReply(q);
        hubChatMessages.push({ sender: "assistant", text: reply });
        renderHubChatThread();
      }, 400);
    });
  }

  // Quick chips in hub
  document.querySelectorAll(".chip-prompt-hub").forEach(chip => {
    chip.addEventListener("click", () => {
      const q = chip.dataset.query;
      hubChatMessages.push({ sender: "user", text: q });
      renderHubChatThread();

      setTimeout(() => {
        const reply = generateHubAssistantReply(q);
        hubChatMessages.push({ sender: "assistant", text: reply });
        renderHubChatThread();
      }, 500);
    });
  });
}


// -------------------------------------------------------------
// New Lead Intake: Mode Switcher (Manual vs CSV Import)
// -------------------------------------------------------------
let parsedCsvLeads = [];

function switchIntakeMode(mode) {
  const manualContainer = document.getElementById("manualIntakeContainer");
  const csvContainer = document.getElementById("csvImportContainer");
  const tabManual = document.getElementById("tabBtnManual");
  const tabCsv = document.getElementById("tabBtnCsv");

  if (mode === "manual") {
    if (manualContainer) manualContainer.style.display = "block";
    if (csvContainer) csvContainer.style.display = "none";
    if (tabManual) tabManual.classList.add("active");
    if (tabCsv) tabCsv.classList.remove("active");
  } else if (mode === "csv") {
    if (manualContainer) manualContainer.style.display = "none";
    if (csvContainer) csvContainer.style.display = "flex";
    if (tabManual) tabManual.classList.remove("active");
    if (tabCsv) tabCsv.classList.add("active");
  }
}

function parseCSVLine(line, delimiter = ",") {
  const result = [];
  let current = "";
  let inQuotes = false;
  for (let i = 0; i < line.length; i++) {
    const char = line[i];
    if (char === '"') {
      if (inQuotes && line[i + 1] === '"') {
        current += '"';
        i++;
      } else {
        inQuotes = !inQuotes;
      }
    } else if (char === delimiter && !inQuotes) {
      result.push(current);
      current = "";
    } else {
      current += char;
    }
  }
  result.push(current);
  return result;
}

function parseCSVText(csvText) {
  if (!csvText || typeof csvText !== "string") return [];

  // 1. Strip UTF-8 Byte Order Mark (BOM) common from Excel
  const cleanText = csvText.replace(/^\uFEFF/, "");

  // 2. Auto-detect delimiter: comma vs semicolon vs tab
  const firstLine = cleanText.split(/\r?\n/)[0] || "";
  let delimiter = ",";
  const commaCount = (firstLine.match(/,/g) || []).length;
  const semiCount = (firstLine.match(/;/g) || []).length;
  const tabCount = (firstLine.match(/\t/g) || []).length;
  if (semiCount > commaCount && semiCount > tabCount) {
    delimiter = ";";
  } else if (tabCount > commaCount && tabCount > semiCount) {
    delimiter = "\t";
  }

  // 3. Robust RFC 4180 character-by-character scanner handling quoted multiline fields
  const rows = [];
  let currentRow = [];
  let currentField = "";
  let inQuotes = false;

  for (let i = 0; i < cleanText.length; i++) {
    const char = cleanText[i];
    const nextChar = cleanText[i + 1];

    if (char === '"') {
      if (inQuotes && nextChar === '"') {
        currentField += '"';
        i++; // skip escaped quote
      } else {
        inQuotes = !inQuotes;
      }
    } else if (char === delimiter && !inQuotes) {
      currentRow.push(currentField);
      currentField = "";
    } else if ((char === '\r' || char === '\n') && !inQuotes) {
      if (char === '\r' && nextChar === '\n') {
        i++; // skip \n in \r\n
      }
      currentRow.push(currentField);
      currentField = "";
      if (currentRow.some(cell => cell.trim().length > 0)) {
        rows.push(currentRow);
      }
      currentRow = [];
    } else {
      currentField += char;
    }
  }

  if (currentField.length > 0 || currentRow.length > 0) {
    currentRow.push(currentField);
    if (currentRow.some(cell => cell.trim().length > 0)) {
      rows.push(currentRow);
    }
  }

  if (rows.length < 2) return [];

  // 4. Normalize and map column headers
  const rawHeaders = rows[0].map(h => h.trim().toLowerCase().replace(/[\s_-]+/g, ""));
  const findIdx = (keywords) => rawHeaders.findIndex(h => keywords.some(k => h.includes(k)));

  const nameIdx = findIdx(["name", "customer", "lead", "client"]);
  const phoneIdx = findIdx(["phone", "mobile", "contact", "tel", "cell", "number"]);
  const locIdx = findIdx(["loc", "area", "city", "place", "address", "zone"]);
  const reqIdx = findIdx(["req", "prop", "type", "unit", "bhk", "config"]);
  const budgetIdx = findIdx(["budg", "price", "cost", "inr", "amount", "val"]);
  const timelineIdx = findIdx(["time", "urgency", "when", "schedule", "period"]);
  const msgIdx = findIdx(["msg", "message", "inquiry", "enquiry", "note", "desc", "comment", "text"]);

  // Need at least one identifying column
  if (nameIdx === -1 && locIdx === -1 && reqIdx === -1) return [];

  const results = [];
  const seenInBatch = new Set();

  for (let r = 1; r < rows.length; r++) {
    const cols = rows[r];
    // Skip empty / blank lines
    if (!cols || cols.every(c => !c || !c.trim())) continue;

    const rawName = (nameIdx !== -1 && cols[nameIdx]) ? cols[nameIdx].trim() : "";
    const rawPhone = (phoneIdx !== -1 && cols[phoneIdx]) ? cols[phoneIdx].trim() : "";
    const rawLoc = (locIdx !== -1 && cols[locIdx]) ? cols[locIdx].trim() : "";
    const rawReq = (reqIdx !== -1 && cols[reqIdx]) ? cols[reqIdx].trim() : "";
    const rawBudget = (budgetIdx !== -1 && cols[budgetIdx]) ? cols[budgetIdx].trim() : "";
    const rawTimeline = (timelineIdx !== -1 && cols[timelineIdx]) ? cols[timelineIdx].trim() : "";
    const rawMsg = (msgIdx !== -1 && cols[msgIdx]) ? cols[msgIdx].trim() : "";

    // Ignore lines that have zero usable content
    if (!rawName && !rawLoc && !rawReq && !rawMsg) continue;

    const finalName = rawName || `Lead #${results.length + 1}`;
    const normalizedPhone = normalizePhoneNumber(rawPhone) || (rawPhone ? rawPhone : "+91 98765 43210");

    // Duplicate detection inside CSV
    const phoneDigits = normalizedPhone.replace(/\D/g, "");
    const duplicateKey = `${finalName.toLowerCase()}|${phoneDigits.slice(-10)}`;
    const isDuplicateInBatch = seenInBatch.has(duplicateKey);
    seenInBatch.add(duplicateKey);

    // Duplicate detection against existing CRM leads
    const isExistingInCrm = (typeof leads !== "undefined" && Array.isArray(leads)) && leads.some(ex => {
      const exName = (ex.name || "").toLowerCase().trim();
      const exPhone = (ex.phone || "").replace(/\D/g, "");
      if (phoneDigits.length >= 10 && exPhone.length >= 10) {
        if (phoneDigits.slice(-10) === exPhone.slice(-10)) return true;
      }
      return exName === finalName.toLowerCase() && (ex.location || "").toLowerCase() === rawLoc.toLowerCase();
    });

    const isDuplicate = isDuplicateInBatch || isExistingInCrm;
    const duplicateReason = isDuplicateInBatch ? "Duplicate in CSV" : (isExistingInCrm ? "Already in CRM" : "");

    results.push({
      name: finalName,
      phone: normalizedPhone,
      location: rawLoc || "Bangalore",
      requirement: rawReq || "2BHK / 3BHK",
      budget: rawBudget || "1.2 Cr",
      timeline: rawTimeline || "Within 1 month",
      message: rawMsg || "Interested in property inspection and detailed cost sheet.",
      is_duplicate: isDuplicate,
      duplicate_reason: duplicateReason
    });
  }

  return results;
}

// Helper functions for lead initials avatar circle
function getLeadInitials(name) {
  if (!name || typeof name !== "string") return "--";
  const clean = name.replace(/[^\w\s]/gi, " ").trim();
  const words = clean.split(/\s+/).filter(w => w.length > 0 && w.toLowerCase() !== "and");
  if (words.length === 0) return "--";
  if (words.length === 1) return words[0].slice(0, 2).toUpperCase();
  const first = words[0][0];
  const last = words[words.length - 1][0];
  return (first + last).toUpperCase();
}

function getLeadAvatarHtml(name, priority, size = "md") {
  const initials = getLeadInitials(name);
  const p = (priority || "warm").toLowerCase();
  return `<span class="lead-avatar-circle ${p} size-${size}" aria-hidden="true">${initials}</span>`;
}

function displayCsvPreview(leadsList) {
  parsedCsvLeads = leadsList || [];
  const previewCard = document.getElementById("csvPreviewCard");
  const previewTitle = document.getElementById("csvPreviewTitle");
  const duplicateBadge = document.getElementById("csvDuplicateCountBadge");
  const tbody = document.getElementById("csvPreviewTableBody");
  const importBtn = document.getElementById("btnImportCsvLeads");

  if (!previewCard || !tbody || !importBtn) return;

  if (!leadsList || leadsList.length === 0) {
    previewCard.style.display = "none";
    if (duplicateBadge) duplicateBadge.style.display = "none";
    importBtn.disabled = true;
    importBtn.innerHTML = "<span>Batch Qualify & Import with AI</span>";
    return;
  }

  const duplicates = leadsList.filter(l => l.is_duplicate);
  const newLeads = leadsList.filter(l => !l.is_duplicate);

  tbody.innerHTML = "";
  leadsList.forEach(lead => {
    const tr = document.createElement("tr");
    if (lead.is_duplicate) {
      tr.style.opacity = "0.75";
      tr.style.background = "#fff1f2";
    }
    tr.innerHTML = `
      <td style="font-weight: 700;">
        <div style="display: flex; align-items: center; gap: 8px;">
          ${getLeadAvatarHtml(lead.name, lead.is_duplicate ? "cold" : "warm", "xs")}
          <span>${lead.name}</span>
        </div>
      </td>
      <td style="font-family: monospace; font-size: 11.5px; color: #047857; font-weight: 600;">${lead.phone || "—"}</td>
      <td>${lead.location}</td>
      <td>${lead.requirement}</td>
      <td style="font-weight: 700; color: #059669;">₹${lead.budget}</td>
      <td>${lead.timeline}</td>
      <td>
        ${lead.is_duplicate
          ? `<span class="csv-status-badge duplicate" title="${lead.duplicate_reason || 'Duplicate'}">⚠ ${lead.duplicate_reason || 'Duplicate'}</span>`
          : `<span class="csv-status-badge new">✓ Valid</span>`
        }
      </td>
    `;
    tbody.appendChild(tr);
  });

  previewTitle.textContent = `Parsed Leads Preview (${leadsList.length} rows)`;
  if (duplicateBadge) {
    if (duplicates.length > 0) {
      duplicateBadge.textContent = `${duplicates.length} duplicate(s) detected`;
      duplicateBadge.style.display = "inline-block";
    } else {
      duplicateBadge.style.display = "none";
    }
  }

  previewCard.style.display = "block";

  if (newLeads.length > 0) {
    importBtn.disabled = false;
    importBtn.innerHTML = `<span>Batch Qualify & Import (${newLeads.length} New Leads)</span>`;
  } else {
    importBtn.disabled = true;
    importBtn.innerHTML = `<span>All ${duplicates.length} Leads Are Duplicates</span>`;
  }
}

function exportLeadsToCsv() {
  const activeFilterBtn = document.querySelector(".filter-tab-btn.active");
  const priorityFilter = activeFilterBtn ? activeFilterBtn.dataset.filter : "all";
  const locSelect = document.getElementById("localityFilterSelect");
  const locFilter = locSelect ? locSelect.value : "all";

  // Filter leads matching current table view
  let exportList = Array.isArray(leads) ? [...leads] : [];
  if (priorityFilter && priorityFilter !== "all") {
    exportList = exportList.filter(l => (l.priority || "").toLowerCase() === priorityFilter.toLowerCase());
  }
  if (locFilter && locFilter !== "all") {
    exportList = exportList.filter(l => (l.location || "").toLowerCase().includes(locFilter.toLowerCase()));
  }

  if (exportList.length === 0) {
    showToast("No leads match current filter to export.");
    return;
  }

  const escapeCsv = (val) => {
    if (val === null || val === undefined) return '""';
    const str = String(val).replace(/"/g, '""');
    return `"${str}"`;
  };

  const headers = [
    "Lead ID",
    "Name",
    "Phone",
    "Priority",
    "Score",
    "Location",
    "Property Requirement",
    "Budget",
    "Timeline",
    "Urgency Action",
    "Inquiry Message",
    "Followup Status",
    "Created At"
  ];

  const lines = [headers.join(",")];
  exportList.forEach(l => {
    const followupStatus = (l.followup && l.followup.status) ? l.followup.status : "pending";
    const row = [
      escapeCsv(l.id || ""),
      escapeCsv(l.name || ""),
      escapeCsv(l.phone || ""),
      escapeCsv(l.priority || "Warm"),
      escapeCsv(l.score || 50),
      escapeCsv(l.location || ""),
      escapeCsv(l.property_requirement || ""),
      escapeCsv(l.budget || ""),
      escapeCsv(l.timeline || ""),
      escapeCsv(l.urgency_label || ""),
      escapeCsv(l.message || ""),
      escapeCsv(followupStatus),
      escapeCsv(l.created_at || new Date().toISOString())
    ];
    lines.push(row.join(","));
  });

  // Prepend UTF-8 BOM so Excel opens with correct character encoding
  const csvContent = "\uFEFF" + lines.join("\r\n");
  const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  const dateStr = new Date().toISOString().slice(0, 10);
  link.setAttribute("href", url);
  link.setAttribute("download", `leads_export_${dateStr}.csv`);
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);

  showToast(`📥 Exported ${exportList.length} leads to CSV successfully!`);
}

function setupCsvHandlers() {
  const dropzone = document.getElementById("csvDropzone");
  const fileInput = document.getElementById("csvFileInput");
  const btnDownloadTemplate = document.getElementById("btnDownloadCsvTemplate");
  const btnLoadSample = document.getElementById("btnLoadSampleCsv");
  const btnClear = document.getElementById("btnClearCsv");
  const btnImport = document.getElementById("btnImportCsvLeads");
  const cancelCsvBtn = document.getElementById("cancelCsvModalBtn");
  const modal = document.getElementById("leadIntakeModal");
  const btnExportCsv = document.getElementById("btnExportLeadsCsv");

  // Export CSV button in leads table toolbar
  if (btnExportCsv) {
    btnExportCsv.addEventListener("click", exportLeadsToCsv);
  }

  // Drag and drop events
  if (dropzone && fileInput) {
    dropzone.addEventListener("click", (e) => {
      // Avoid double trigger if clicking the explicit browse link
      if (e.target && e.target.classList && e.target.classList.contains("dropzone-browse-text")) {
        return;
      }
      fileInput.click();
    });
    dropzone.addEventListener("dragover", (e) => {
      e.preventDefault();
      dropzone.classList.add("dragover");
    });
    dropzone.addEventListener("dragleave", () => {
      dropzone.classList.remove("dragover");
    });
    dropzone.addEventListener("drop", (e) => {
      e.preventDefault();
      dropzone.classList.remove("dragover");
      if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
        handleCsvFile(e.dataTransfer.files[0]);
      }
    });

    fileInput.addEventListener("change", (e) => {
      if (e.target.files && e.target.files.length > 0) {
        handleCsvFile(e.target.files[0]);
      }
    });
  }

  function handleCsvFile(file) {
    if (!file.name.toLowerCase().endsWith(".csv")) {
      showToast("Please upload a valid .csv file");
      return;
    }
    const reader = new FileReader();
    reader.onload = (e) => {
      const parsed = parseCSVText(e.target.result);
      if (parsed.length === 0) {
        showToast("Could not find valid lead rows in CSV file.");
      } else {
        displayCsvPreview(parsed);
        const dupCount = parsed.filter(l => l.is_duplicate).length;
        const dupNote = dupCount ? ` (${dupCount} duplicate(s) flagged)` : "";
        showToast(`Loaded ${parsed.length} rows from ${file.name}${dupNote}`);
      }
    };
    reader.readAsText(file);
  }

  // Clear preview
  if (btnClear) {
    btnClear.addEventListener("click", () => {
      displayCsvPreview([]);
      if (fileInput) fileInput.value = "";
    });
  }

  // Cancel CSV
  if (cancelCsvBtn && modal) {
    cancelCsvBtn.addEventListener("click", () => {
      modal.style.display = "none";
      displayCsvPreview([]);
    });
  }

  // Download Sample Template
  if (btnDownloadTemplate) {
    btnDownloadTemplate.addEventListener("click", () => {
      const sampleCsv = `name,phone,location,requirement,budget,timeline,message\r\n` +
        `Vikram Singhania,+91 98765 43210,Whitefield,3BHK ready to move,1.6 Cr,Within 1 month,"Looking for ready to move 3BHK flat near ITPL. Loan sanctioned from HDFC, immediate registration."\r\n` +
        `Ananya Sharma,+91 98111 22334,Sarjapur Road,2BHK,85 L,2-3 months,"Need a 2BHK in gated community near Sarjapur Road with good amenities for children."\r\n` +
        `Karan Patel,+91 99000 88776,Hebbal,4BHK Luxury Penthouse,3.5 Cr,1-2 months,"Looking for high-floor luxury penthouse with panoramic lake view and 2 covered car parks."\r\n` +
        `Nikhil Verma,+91 97400 55667,Electronic City,1BHK / Studio,45 L,Within 1 month,"Looking for compact unit for rental yield near tech hubs, immediate payment ready."\r\n` +
        `Divya Menon,+91 96320 11223,Kanakapura Road,3BHK Villa,2.1 Cr,3-6 months,"Planning retirement villa with private garden near metro station, seeking RERA verified project."`;

      const blob = new Blob(["\uFEFF" + sampleCsv], { type: "text/csv;charset=utf-8;" });
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.setAttribute("href", url);
      link.setAttribute("download", "sample_leads_template.csv");
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
      showToast("Downloaded sample_leads_template.csv");
    });
  }

  // Load Benchmark Sample CSV (5 leads directly into preview)
  if (btnLoadSample) {
    btnLoadSample.addEventListener("click", () => {
      const sampleLeads = [
        {
          name: "Vikram Singhania",
          phone: "+91 98765 43210",
          location: "Whitefield",
          requirement: "3BHK ready to move",
          budget: "1.6 Cr",
          timeline: "Within 1 month",
          message: "Looking for ready to move 3BHK flat near ITPL. Loan sanctioned from HDFC for 1.2 Cr, immediate registration."
        },
        {
          name: "Ananya Sharma",
          phone: "+91 98111 22334",
          location: "Sarjapur Road",
          requirement: "2BHK",
          budget: "85 L",
          timeline: "2-3 months",
          message: "Need a 2BHK in gated community near Sarjapur Road with good amenities for children."
        },
        {
          name: "Karan Patel",
          phone: "+91 99000 88776",
          location: "Hebbal",
          requirement: "4BHK Luxury Penthouse",
          budget: "3.5 Cr",
          timeline: "1-2 months",
          message: "Looking for high-floor luxury penthouse with panoramic lake view and 2 covered car parks."
        },
        {
          name: "Nikhil Verma",
          phone: "+91 97400 55667",
          location: "Electronic City",
          requirement: "1BHK / Studio",
          budget: "45 L",
          timeline: "Within 1 month",
          message: "Looking for compact unit for rental yield near tech hubs, immediate payment ready."
        },
        {
          name: "Divya Menon",
          phone: "+91 96320 11223",
          location: "Kanakapura Road",
          requirement: "3BHK Villa",
          budget: "2.1 Cr",
          timeline: "3-6 months",
          message: "Planning retirement villa with private garden near metro station, seeking RERA verified project."
        }
      ];

      // Re-run through duplication check against CRM
      sampleLeads.forEach(sl => {
        const phoneDigits = (sl.phone || "").replace(/\D/g, "");
        const isExistingInCrm = (typeof leads !== "undefined" && Array.isArray(leads)) && leads.some(ex => {
          const exName = (ex.name || "").toLowerCase().trim();
          const exPhone = (ex.phone || "").replace(/\D/g, "");
          if (phoneDigits.length >= 10 && exPhone.length >= 10) {
            if (phoneDigits.slice(-10) === exPhone.slice(-10)) return true;
          }
          return exName === sl.name.toLowerCase();
        });
        sl.is_duplicate = isExistingInCrm;
        sl.duplicate_reason = isExistingInCrm ? "Already in CRM" : "";
      });

      displayCsvPreview(sampleLeads);
      showToast("Loaded 5 benchmark test leads into preview!");
    });
  }

  // Batch Qualify & Import
  if (btnImport) {
    btnImport.addEventListener("click", async () => {
      const leadsToImport = parsedCsvLeads.filter(l => !l.is_duplicate);
      if (leadsToImport.length === 0) {
        showToast("No new leads to import (all detected as duplicates).");
        return;
      }

      btnImport.disabled = true;
      btnImport.innerHTML = "<span>AI Qualifying & Scoring Leads...</span>";

      // 1. Try Flask API batch endpoint
      try {
        const payload = leadsToImport.map(raw => ({
          name: raw.name,
          phone: raw.phone,
          location: raw.location,
          property_requirement: raw.requirement,
          budget: raw.budget,
          timeline: raw.timeline,
          message: raw.message
        }));

        const res = await fetch("/api/leads/batch", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ leads: payload, skip_duplicates: true })
        });

        if (res.ok) {
          const data = await res.json();
          if (data.success && Array.isArray(data.leads) && data.leads.length > 0) {
            leads.unshift(...data.leads);
            modal.style.display = "none";
            displayCsvPreview([]);
            if (fileInput) fileInput.value = "";
            btnImport.disabled = false;
            btnImport.innerHTML = "<span>Batch Qualify & Import with AI</span>";

            updateGlobalMetrics();
            if (activePage === "leadsPage") renderLeadsTable();
            else if (activePage === "dashboardPage") renderDashboard();
            else if (activePage === "pipelinePage") renderKanbanPipeline();

            const skippedMsg = data.skipped_duplicates ? ` (${data.skipped_duplicates} duplicate(s) skipped)` : "";
            showToast(`🎉 Successfully imported and AI-scored ${data.leads.length} leads${skippedMsg}!`);
            return;
          }
        }
      } catch (err) {
        console.log("[CSV API] Offline, using client-side engine:", err);
      }

      // 2. Client-side fallback with correct argument order
      setTimeout(() => {
        let count = 0;
        leadsToImport.forEach(raw => {
          const newLead = createEvaluatedLead(
            raw.name,
            raw.phone,
            raw.location,
            raw.requirement,
            raw.budget,
            raw.timeline,
            raw.message
          );
          leads.unshift(newLead);
          count++;
        });

        // Close modal and reset
        modal.style.display = "none";
        displayCsvPreview([]);
        if (fileInput) fileInput.value = "";
        btnImport.disabled = false;
        btnImport.innerHTML = "<span>Batch Qualify & Import with AI</span>";

        // Update application
        updateGlobalMetrics();
        if (activePage === "leadsPage") {
          renderLeadsTable();
        } else if (activePage === "dashboardPage") {
          renderDashboard();
        } else if (activePage === "pipelinePage") {
          renderKanbanPipeline();
        }

        showToast(`🎉 Successfully imported and AI-scored ${count} leads from CSV!`);
      }, 700);
    });
  }
}

/**
 * Masal AI - Real Estate Sales Copilot
 * Multi-Page SPA Engine (Sidebar, Dashboard, Leads Directory, Full Lead Dossier, Pipeline, Follow-Up Hub)
 */

// App State (holds only real leads from Firebase Firestore / database)
let leads = [];
let currentLeadId = null;
let activePage = "dashboardPage";
let currentTableFilter = "all";

// DOM Elements Initialization
document.addEventListener("DOMContentLoaded", () => {
  setupNavigation();
  setupEventListeners();
  renderDashboard();
  renderLeadsTable();
  renderKanbanPipeline();
  renderFollowupHub();
  setupDonutHover();
  setupResizablePanels();
  updateGlobalMetrics();
  syncWithBackend();
});

async function syncWithBackend() {
  try {
    const resLeads = await fetch("/api/leads");
    if (resLeads.ok) {
      const data = await resLeads.json();
      if (data.success && Array.isArray(data.leads)) {
        leads = data.leads;
        if (leads.length > 0 && !currentLeadId) {
          currentLeadId = leads[0].id;
        }
        renderDashboard();
        renderLeadsTable();
        renderKanbanPipeline();
        renderFollowupHub();
        updateGlobalMetrics();
        console.log(`[Backend Sync] Loaded ${leads.length} real leads.`);
      }
    }
  } catch (err) {
    console.log("[Backend Sync] Running in local standalone mode.");
  }
}

// -------------------------------------------------------------
// Navigation & Page Switching
// -------------------------------------------------------------
function setupNavigation() {
  const navItems = document.querySelectorAll(".sidebar-nav .nav-item");

  navItems.forEach(item => {
    item.addEventListener("click", () => {
      const targetPage = item.dataset.page;
      navigateToPage(targetPage);
    });
  });

  // Back button from detail page
  const backBtn = document.getElementById("backToLeadsBtn");
  if (backBtn) {
    backBtn.addEventListener("click", () => {
      navigateToPage("leadsPage");
    });
  }
}

function navigateToPage(pageId) {
  // Update sidebar active state
  document.querySelectorAll(".sidebar-nav .nav-item").forEach(btn => {
    btn.classList.toggle("active", btn.dataset.page === pageId);
  });

  // Switch page views
  document.querySelectorAll(".page-view").forEach(view => {
    view.classList.toggle("active", view.id === pageId);
  });

  activePage = pageId;

  // Update top header title
  const titleHeading = document.getElementById("pageTitleHeading");
  const breadcrumb = document.getElementById("pageBreadcrumb");

  if (pageId === "dashboardPage") {
    titleHeading.textContent = "Executive Dashboard";
    breadcrumb.textContent = "Pipeline Overview & High-Value Queue";
    renderDashboard();
  } else if (pageId === "leadsPage") {
    titleHeading.textContent = "All Leads Directory";
    breadcrumb.textContent = "CRM Database • Filter by Priority, Location & Budget";
    renderLeadsTable();
  } else if (pageId === "pipelinePage") {
    titleHeading.textContent = "Sales Pipeline";
    breadcrumb.textContent = "Visual Kanban Stages • Hot / Warm / Cold / Due";
    renderKanbanPipeline();
  } else if (pageId === "followupsPage") {
    titleHeading.textContent = "AI Follow-Up Assistant";
    breadcrumb.textContent = "Scheduled Reminders & Personalized Touchpoint Generator";
    renderFollowupHub();
    setupDonutHover();
      } else if (pageId === "leadDetailPage") {
    const lead = leads.find(l => l.id === currentLeadId) || leads[0];
    if (lead) {
      titleHeading.textContent = lead.name;
      breadcrumb.textContent = `Priority: ${lead.priority} (${lead.score}/100) • Stated Budget: ₹${lead.budget}`;
      renderFullLeadDossier(lead.id);
    } else {
      titleHeading.textContent = "Lead Dossier";
      breadcrumb.textContent = "No leads in database";
      renderFullLeadDossier(null);
    }
  }
}

function openLeadDetail(leadId) {
  currentLeadId = leadId;
  navigateToPage("leadDetailPage");
}

// -------------------------------------------------------------
// Page 1: Dashboard Rendering
// -------------------------------------------------------------
function renderDashboard() {
  const queueList = document.getElementById("dashActionQueueList");
  const remindersSummary = document.getElementById("dashRemindersSummary");

  // Top action queue: Hot leads
  const hotLeads = leads.filter(l => l.priority === "Hot");
  queueList.innerHTML = "";

  if (hotLeads.length === 0) {
    queueList.innerHTML = `
      <div style="padding: 24px; text-align: center; color: #64748b; font-size: 13px;">
        No Hot leads in queue right now.
      </div>
    `;
  }

  hotLeads.forEach(lead => {
    const item = document.createElement("div");
    item.className = "queue-item-card";
    item.onclick = () => openLeadDetail(lead.id);

    item.innerHTML = `
      <div class="queue-item-left">
        ${getLeadAvatarHtml(lead.name, lead.priority, "md")}
        <div class="queue-item-info">
          <div class="queue-item-name">
            <span>${lead.name}</span>
            <span class="badge-tag hot">HOT ${lead.score}</span>
          </div>
          <div class="queue-item-meta">
            ${lead.location} <span class="meta-sep">·</span> ${lead.property_requirement.split(",")[0]} <span class="meta-sep">·</span> ₹${lead.budget} <span class="meta-sep">·</span> ${lead.timeline}
          </div>
        </div>
      </div>
      <div class="queue-item-right">
        <div class="queue-item-action">${lead.urgency_label}</div>
        <button class="btn-open-dossier" onclick="event.stopPropagation(); openLeadDetail('${lead.id}')">Open</button>
      </div>
    `;
    queueList.appendChild(item);
  });

  // Scheduled reminders summary (Follow-Up Desk)
  const dueLeads = leads.filter(l => l.followup && l.followup.status === "due");
  remindersSummary.innerHTML = "";

  if (dueLeads.length === 0) {
    remindersSummary.innerHTML = `
      <div style="padding: 24px; text-align: center; color: #64748b; font-size: 13px;">
        No pending follow-ups due right now.
      </div>
    `;
  }

  dueLeads.forEach(lead => {
    const row = document.createElement("div");
    row.className = "dash-reminder-row";
    row.onclick = () => openLeadDetail(lead.id);

    const goal = (lead.followup && lead.followup.goal) || "Confirm property visit & requirements";
    const rawDue = (lead.followup && (lead.followup.due || lead.followup.scheduled || lead.followup.time_badge)) || "Today by 4:00 PM";
    const timeDisplay = rawDue.replace("Today by ", "").replace("Today, ", "");

    row.innerHTML = `
      <div style="display: flex; align-items: center; gap: 10px;">
        ${getLeadAvatarHtml(lead.name, lead.priority, "sm")}
        <div>
          <div style="font-weight: 800; font-size: 13.5px; color: #000000;">${lead.name} <span class="lead-location-sub" style="margin-left: 6px;">· ${lead.location}</span></div>
          <div style="font-size: 12px; color: #555555; font-weight: 500; margin-top: 2px;">${goal}</div>
        </div>
      </div>
      <div style="text-align: right; display: flex; flex-direction: column; align-items: flex-end; justify-content: center; gap: 4px;">
        <span style="color: #334155; font-weight: 700; font-size: 12px; white-space: nowrap;">${timeDisplay}</span>
        <button class="btn-open-dossier" onclick="event.stopPropagation(); openLeadDetail('${lead.id}')">Open</button>
      </div>
    `;
    remindersSummary.appendChild(row);
  });
}

// -------------------------------------------------------------
// Page 2: Leads Directory (CRM Table)
// -------------------------------------------------------------
function renderLeadsTable() {
  const tbody = document.getElementById("leadsTableBody");
  const localitySelect = document.getElementById("localityFilterSelect");
  const sortSelect = document.getElementById("sortSelect");
  const globalQuery = (document.getElementById("globalSearchInput").value || "").toLowerCase().trim();

  const selectedLocality = localitySelect ? localitySelect.value : "all";
  const selectedSort = sortSelect ? sortSelect.value : "score_desc";

  let filtered = leads.filter(lead => {
    const matchesPriority = (currentTableFilter === "all") || (lead.priority === currentTableFilter);
    const matchesLocality = (selectedLocality === "all") || lead.location.toLowerCase().includes(selectedLocality.toLowerCase());
    const matchesQuery = !globalQuery || 
      lead.name.toLowerCase().includes(globalQuery) || 
      lead.location.toLowerCase().includes(globalQuery) ||
      lead.property_requirement.toLowerCase().includes(globalQuery);

    return matchesPriority && matchesLocality && matchesQuery;
  });

  // Sorting
  if (selectedSort === "score_desc") {
    filtered.sort((a, b) => b.score - a.score);
  } else if (selectedSort === "score_asc") {
    filtered.sort((a, b) => a.score - b.score);
  } else if (selectedSort === "urgency") {
    filtered.sort((a, b) => {
      const aVal = (a.breakdown && a.breakdown.timeline && a.breakdown.timeline.score) || (a.score_breakdown && a.score_breakdown.timeline && a.score_breakdown.timeline.score) || 0;
      const bVal = (b.breakdown && b.breakdown.timeline && b.breakdown.timeline.score) || (b.score_breakdown && b.score_breakdown.timeline && b.score_breakdown.timeline.score) || 0;
      return bVal - aVal;
    });
  }

  tbody.innerHTML = "";

  if (filtered.length === 0) {
    tbody.innerHTML = `<tr><td colspan="7" style="text-align: center; padding: 28px; color: var(--text-light); font-size: 13px;">No real leads found. Click "+ New Lead" to add a lead or upload a CSV.</td></tr>`;
    return;
  }

  filtered.forEach(lead => {
    const tr = document.createElement("tr");
    tr.style.cursor = "pointer";
    tr.onclick = (e) => {
      // Don't trigger if clicked on a specific button inside
      if (!e.target.closest("button")) {
        openLeadDetail(lead.id);
      }
    };

    const tagClass = lead.priority.toLowerCase();

    tr.innerHTML = `
      <td>
        <div style="display: flex; align-items: center; gap: 10px;">
          ${getLeadAvatarHtml(lead.name, lead.priority, "sm")}
          <div class="table-lead-name">
            <span>${lead.name}</span>
            <span class="table-lead-id">ID: #${lead.id}${lead.phone ? ` · 📞 ${lead.phone}` : ''}</span>
          </div>
        </div>
      </td>
      <td>
        <div class="score-cell-badge">
          <span class="badge-tag ${tagClass}">${lead.priority.toUpperCase()}</span>
          <span class="table-score-val">${lead.score}/100</span>
        </div>
      </td>
      <td>
        <div><span style="font-weight: 600; color: var(--text-main);">${lead.location}</span></div>
        <div style="font-size: 11.5px; color: var(--text-muted);">${lead.property_requirement}</div>
      </td>
      <td>
        <strong style="color: #000000; font-weight: 800;">₹${lead.budget || "Unspecified"}</strong>
      </td>
      <td>
        <span>${lead.timeline || "Not decided"}</span>
      </td>
      <td>
        <div style="font-size: 12px; color: var(--text-muted); max-width: 260px;">${lead.ai_analysis.next_action.slice(0, 75)}...</div>
      </td>
      <td style="text-align: right;">
        <button class="btn-open-dossier" onclick="openLeadDetail('${lead.id}')">Open</button>
      </td>
    `;
    tbody.appendChild(tr);
  });
}

// -------------------------------------------------------------
// Page 3: Dedicated Full Lead Dossier Rendering
// -------------------------------------------------------------
function renderFullLeadDossier(leadId) {
  const lead = leads.find(l => l.id === leadId) || leads[0];
  if (!lead) {
    const hero = document.getElementById("detailHeroCard");
    if (hero) {
      hero.innerHTML = `
        <div style="padding: 30px; text-align: center; color: #64748b;">
          <h3 style="font-size: 16px; font-weight: 700; color: #1e293b;">No Lead Selected</h3>
          <p style="font-size: 13px; margin-top: 6px;">Select a real lead from the Dashboard or All Leads directory.</p>
        </div>
      `;
    }
    return;
  }
  currentLeadId = lead.id;

  // 1. Breadcrumb ID
  const breadcrumbId = document.getElementById("detailBreadcrumbId");
  if (breadcrumbId) breadcrumbId.textContent = `Lead ID: #${lead.id}`;

  // 2. Hero Card
  const hero = document.getElementById("detailHeroCard");
  const tagClass = (lead.priority || "warm").toLowerCase();
  if (hero) {
    hero.innerHTML = `
      <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 14px;">
        <div style="display: flex; align-items: center; gap: 14px;">
          ${getLeadAvatarHtml(lead.name, lead.priority, "lg")}
          <div>
            <h2 style="font-size: 22px; font-weight: 800; color: #000000; display: flex; align-items: center; gap: 10px;">
              <span>${lead.name}</span>
              <span class="badge-tag ${tagClass}">${(lead.priority || "WARM").toUpperCase()}</span>
            </h2>
            <div style="font-size: 13px; color: #000000; font-weight: 600; margin-top: 4px;">
              ${lead.location} <span class="meta-sep">·</span> ${lead.property_requirement}
            </div>
            ${lead.phone ? `
            <div style="margin-top: 6px; display: flex; flex-direction: column; align-items: flex-start; gap: 4px;">
              <span style="display: inline-flex; align-items: center; gap: 5px; color: #059669; font-weight: 700; font-size: 12.5px; white-space: nowrap;">
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" style="flex-shrink: 0;"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"></path></svg>
                <a href="tel:${lead.phone.replace(/\s+/g, '')}" style="color: #047857; text-decoration: none; font-weight: 700; white-space: nowrap;">${lead.phone}</a>
              </span>
              <a href="https://wa.me/${lead.phone.replace(/\D/g, '')}" target="_blank" rel="noopener noreferrer" style="font-size: 11px; background: #ecfdf5; color: #059669; border: 1px solid #a7f3d0; padding: 2px 10px; border-radius: 999px; text-decoration: none; font-weight: 700; white-space: nowrap; display: inline-flex; align-items: center; gap: 4px;">WhatsApp</a>
            </div>
            ` : ''}
          </div>
        </div>
        <div style="text-align: right;">
          <div style="font-size: 26px; font-weight: 800; color: #000000; line-height: 1;">${lead.score}<span style="font-size: 14px; font-weight: 700; color: #222222;">/100</span></div>
        </div>
      </div>

      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; background: #f8fafc; border: 1px solid #e2e8f0; padding: 12px 14px; border-radius: var(--radius-md);">
        <div>
          <span style="font-size: 11px; color: #222222; font-weight: 700; text-transform: uppercase;">Stated Budget:</span>
          <div style="font-weight: 800; font-size: 15px; color: #000000; margin-top: 2px;">₹${lead.budget || "Unspecified"}</div>
        </div>
        <div>
          <span style="font-size: 11px; color: #222222; font-weight: 700; text-transform: uppercase;">Buying Timeline:</span>
          <div style="font-weight: 800; font-size: 15px; color: #000000; margin-top: 2px;">${lead.timeline || "Not decided"}</div>
        </div>
      </div>
    `;
  }

  // 3. 6-Factor Score Card (supports both lead.breakdown and lead.score_breakdown)
  const scoreCard = document.getElementById("detailScoreCard");
  const b = lead.breakdown || lead.score_breakdown || {};
  if (scoreCard) {
    scoreCard.innerHTML = `
      <div class="card-header-clean">
        <span class="card-title-sm">6-Factor Lead Breakdown</span>
      </div>
      <div class="score-bars-compact">
        ${renderCompactFactor(b.timeline)}
        ${renderCompactFactor(b.budget)}
        ${renderCompactFactor(b.intent)}
        ${renderCompactFactor(b.requirement)}
        ${renderCompactFactor(b.engagement)}
        ${renderCompactFactor(b.readiness)}
      </div>
    `;
  }

  // 4. Raw Message
  const rawMsg = document.getElementById("detailRawMessage");
  if (rawMsg) rawMsg.textContent = lead.message ? `"${lead.message}"` : '"Inbound customer inquiry submitted."';

  // 5. AI Intelligence
  const ai = lead.ai_analysis || {};
  const summaryEl = document.getElementById("detailAiSummary");
  if (summaryEl) summaryEl.textContent = ai.summary || `${lead.name} inquiring for ${lead.property_requirement} in ${lead.location}.`;

  const intentEl = document.getElementById("detailAiIntent");
  if (intentEl) intentEl.textContent = ai.intent || "Active interest in Bangalore property matching stated budget & timeline.";

  const reqEl = document.getElementById("detailAiRequirements");
  if (reqEl) reqEl.textContent = ai.requirements || `${lead.property_requirement} in ${lead.location}`;

  const objectionsList = document.getElementById("detailAiObjections");
  if (objectionsList) {
    const objs = ai.objections && Array.isArray(ai.objections) && ai.objections.length > 0
      ? ai.objections
      : ["Clear documentation & OC verification", "Cost sheet with registration breakdown"];
    objectionsList.innerHTML = objs.map(o => `<li class="objection-item"><span class="bullet-dot">•</span> <span>${o}</span></li>`).join("");
  }

  const nextActionEl = document.getElementById("detailAiNextAction");
  if (nextActionEl) nextActionEl.textContent = ai.next_action || (lead.urgency_label || "Call within 24h to verify requirements.");

  const suggestedReplyEl = document.getElementById("detailAiSuggestedReply");
  if (suggestedReplyEl) suggestedReplyEl.textContent = ai.suggested_response || `Hi ${lead.name.split(' ')[0]}, thank you for reaching out! We have units matching your criteria in ${lead.location}. When can we connect?`;

  // 6. Follow-up Assistant Card
  if (lead.followup) {
    const cadenceEl = document.getElementById("detailFollowupCadence");
    if (cadenceEl) cadenceEl.textContent = `Cadence: ${lead.followup.cadence || (lead.priority === 'Hot' ? 'Every 24 hours' : 'Every 48-72 hours')}`;
    const dueEl = document.getElementById("detailFollowupDue");
    if (dueEl) dueEl.textContent = lead.followup.due || lead.followup.scheduled || "Today by 4:00 PM";
    const goalEl = document.getElementById("detailFollowupGoal");
    if (goalEl) goalEl.textContent = lead.followup.goal || "Follow-up with customer";
    const windowEl = document.getElementById("detailFollowupWindow");
    if (windowEl) windowEl.textContent = lead.followup.window || "Immediate / Afternoon";
    const textEl = document.getElementById("detailFollowupText");
    if (textEl) textEl.value = lead.followup.template || `Hi ${lead.name.split(' ')[0]}, following up on your inquiry for ${lead.location}. When would be a good time to connect?`;
  }

  // 7. Render Copilot Thread
  renderDetailChatThread(lead);
}

function renderCompactFactor(factor) {
  if (!factor || typeof factor.score === "undefined" || !factor.max) return "";
  const pct = Math.round((factor.score / factor.max) * 100);
  return `
    <div style="display: flex; flex-direction: column; gap: 2px;">
      <div style="display: flex; justify-content: space-between; font-size: 11px; font-weight: 600;">
        <span style="color: var(--text-muted);">${factor.label}</span>
        <span style="font-family: 'JetBrains Mono';">${factor.score}/${factor.max}</span>
      </div>
      <div style="width: 100%; height: 5px; background: #e2e8f0; border-radius: 999px; overflow: hidden;">
        <div style="height: 100%; width: ${pct}%; background: var(--emerald-500); border-radius: 999px;"></div>
      </div>
    </div>
  `;
}

function renderDetailChatThread(lead) {
  const container = document.getElementById("detailChatThread");
  if (!container) return;
  container.innerHTML = "";

  if (!lead.chat_history || !Array.isArray(lead.chat_history) || lead.chat_history.length === 0) {
    lead.chat_history = [
      {
        sender: "assistant",
        text: `I have analyzed **${lead.name}** (${lead.priority} Lead, Score: ${lead.score}/100). Ask me anything about their inquiry, requirements, objections, or strategy in English or Hinglish!`
      }
    ];
  }

  lead.chat_history.forEach(msg => {
    const bubble = document.createElement("div");
    bubble.className = `bubble ${msg.sender}`;
    const textFormatted = (msg.text || "")
      .replace(/\n/g, "<br>")
      .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
      .replace(/\*(.*?)\*/g, "<em>$1</em>");
    bubble.innerHTML = `
      <div style="font-size: 10px; font-weight: 700; text-transform: uppercase; color: var(--emerald-600); margin-bottom: 2px;">
        ${msg.sender === "user" ? "SALES AGENT" : "LEAD COPILOT"}
      </div>
      <div>${textFormatted}</div>
    `;
    container.appendChild(bubble);
  });
  container.scrollTop = container.scrollHeight;
}

// -------------------------------------------------------------
// Page 4: Sales Pipeline (Kanban Board)
// -------------------------------------------------------------
function renderKanbanPipeline() {
  const hotList = document.getElementById("kanbanHotList");
  const warmList = document.getElementById("kanbanWarmList");
  const coldList = document.getElementById("kanbanColdList");
  const dueList = document.getElementById("kanbanDueList");

  hotList.innerHTML = "";
  warmList.innerHTML = "";
  coldList.innerHTML = "";
  dueList.innerHTML = "";

  leads.forEach(lead => {
    const card = document.createElement("div");
    card.className = "kanban-card";
    card.onclick = () => openLeadDetail(lead.id);

    card.innerHTML = `
      <div class="kanban-card-top">
        <div style="display: flex; align-items: center; gap: 8px;">
          ${getLeadAvatarHtml(lead.name, lead.priority, "xs")}
          <span class="k-name">${lead.name}</span>
        </div>
        <span class="k-score">${lead.score} pts</span>
      </div>
      <div class="k-meta">${lead.location} · ₹${lead.budget || 'N/A'}</div>
      <div class="k-action"><span class="action-tag">${lead.urgency_label}</span></div>
    `;

    if (lead.priority === "Hot") {
      hotList.appendChild(card);
    } else if (lead.priority === "Warm") {
      warmList.appendChild(card);
    } else if (lead.priority === "Cold") {
      coldList.appendChild(card);
    }

    // Also place in due column if status is due
    if (lead.followup && lead.followup.status === "due") {
      const dueCard = card.cloneNode(true);
      dueCard.onclick = () => openLeadDetail(lead.id);
      dueList.appendChild(dueCard);
    }
  });

  document.getElementById("kanbanHotCount").textContent = leads.filter(l => l.priority === "Hot").length;
  document.getElementById("kanbanWarmCount").textContent = leads.filter(l => l.priority === "Warm").length;
  document.getElementById("kanbanColdCount").textContent = leads.filter(l => l.priority === "Cold").length;
  document.getElementById("kanbanDueCount").textContent = leads.filter(l => l.followup && l.followup.status === "due").length;

  if (hotList.children.length === 0) hotList.innerHTML = '<div style="padding: 16px; text-align: center; color: #94a3b8; font-size: 12px;">No hot leads</div>';
  if (warmList.children.length === 0) warmList.innerHTML = '<div style="padding: 16px; text-align: center; color: #94a3b8; font-size: 12px;">No warm leads</div>';
  if (coldList.children.length === 0) coldList.innerHTML = '<div style="padding: 16px; text-align: center; color: #94a3b8; font-size: 12px;">No cold leads</div>';
  if (dueList.children.length === 0) dueList.innerHTML = '<div style="padding: 16px; text-align: center; color: #94a3b8; font-size: 12px;">No due follow-ups</div>';
}

// -------------------------------------------------------------
// Page 5: Dedicated Follow-Up Hub
// -------------------------------------------------------------
function renderFollowupHub() {
  const container = document.getElementById("hubFollowupList");
  container.innerHTML = "";

  const dueLeads = leads.filter(l => l.followup && l.followup.status === "due");

  if (dueLeads.length === 0) {
    container.innerHTML = `
      <div style="padding: 30px; text-align: center; color: #64748b; font-size: 13.5px;">
        All scheduled follow-ups are completed!
      </div>
    `;
    return;
  }

  dueLeads.forEach(lead => {
    const row = document.createElement("div");
    row.className = "hub-item-row";

    const goal = (lead.followup && lead.followup.goal) || "Confirm property visit";
    const windowStr = (lead.followup && lead.followup.window) || "Immediate / Afternoon";
    const dueStr = (lead.followup && (lead.followup.due || lead.followup.scheduled || "Today by 4:00 PM"));
    const priorityStr = (lead.priority || "WARM").toUpperCase();
    const priorityClass = (lead.priority || "warm").toLowerCase();

    row.innerHTML = `
      <div style="display: flex; align-items: center; gap: 12px;">
        ${getLeadAvatarHtml(lead.name, lead.priority, "md")}
        <div>
          <div style="font-weight: 700; font-size: 14px; color: var(--text-main); display: flex; align-items: center; gap: 8px;">
            <span>${lead.name}</span> <span class="badge-tag ${priorityClass}">${priorityStr}</span>
          </div>
          <div style="font-size: 12px; color: var(--text-muted); margin-top: 2px;">
            Objective: <strong>${goal}</strong> • Preferred: ${windowStr}
          </div>
          <div style="font-size: 11px; color: #b91c1c; font-weight: 700; margin-top: 2px;">
            Scheduled: ${dueStr}
          </div>
        </div>
      </div>
      <div style="display: flex; flex-direction: column; align-items: flex-end; justify-content: center; gap: 5px; flex-shrink: 0;">
        <button class="btn-hub-action-primary" onclick="openLeadDetail('${lead.id}')">Execute Follow-Up →</button>
        <button class="btn-hub-action-secondary" onclick="showToast('Reminder rescheduled for +24 hours')">Reschedule</button>
      </div>
    `;
    container.appendChild(row);
  });
}

// -------------------------------------------------------------
// Global Updates & Counters
// -------------------------------------------------------------
function updateGlobalMetrics() {
  const total = leads.length;
  const hot = leads.filter(l => l.priority === "Hot").length;
  const warm = leads.filter(l => l.priority === "Warm").length;
  const cold = leads.filter(l => l.priority === "Cold").length;
  const due = leads.filter(l => l.followup && l.followup.status === "due").length;

  // Header badges
  const hdrHot = document.getElementById("hdrHotCount");
  if (hdrHot) hdrHot.textContent = hot;
  const hdrWarm = document.getElementById("hdrWarmCount");
  if (hdrWarm) hdrWarm.textContent = warm;
  const hdrDue = document.getElementById("hdrDueCount");
  if (hdrDue) hdrDue.textContent = due;

  // Sidebar badges
  const bDash = document.getElementById("badgeDashboardTotal");
  if (bDash) bDash.textContent = total;
  const bHot = document.getElementById("badgeLeadsHot");
  if (bHot) bHot.textContent = `${hot} Hot`;
  const bDue = document.getElementById("badgeDueFollowups");
  if (bDue) bDue.textContent = `${due} Due`;

  // Dashboard KPI cards
  const kpiTotal = document.getElementById("kpiTotal");
  if (kpiTotal) {
    kpiTotal.textContent = total;
    const kHot = document.getElementById("kpiHot");
    if (kHot) kHot.textContent = hot;
    const kWarm = document.getElementById("kpiWarm");
    if (kWarm) kWarm.textContent = warm;
    const kDue = document.getElementById("kpiDue");
    if (kDue) kDue.textContent = due;
  }

  // Filter tabs
  const tabAll = document.querySelector('[data-filter="all"]');
  if (tabAll) tabAll.textContent = `All Leads (${total})`;
  const tabHot = document.querySelector('[data-filter="Hot"]');
  if (tabHot) tabHot.textContent = `Hot (${hot})`;
  const tabWarm = document.querySelector('[data-filter="Warm"]');
  if (tabWarm) tabWarm.textContent = `Warm (${warm})`;
  const tabCold = document.querySelector('[data-filter="Cold"]');
  if (tabCold) tabCold.textContent = `Cold (${cold})`;

  // Priority Status Distribution Chart & Metrics
  updatePriorityDistribution();
}

// -------------------------------------------------------------
// Event Handlers & Modal Interactions
// -------------------------------------------------------------
function setupEventListeners() {
  setupHubChat();
  setupCsvHandlers();
  // Global search input
  const globalSearch = document.getElementById("globalSearchInput");
  if (globalSearch) {
    globalSearch.addEventListener("input", () => {
      if (activePage === "leadsPage") {
        renderLeadsTable();
      } else {
        navigateToPage("leadsPage");
      }
    });
  }

  // Leads toolbar filter buttons
  document.querySelectorAll(".filter-tab-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".filter-tab-btn").forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      currentTableFilter = btn.dataset.filter;
      renderLeadsTable();
    });
  });

  // Locality & Sort Select
  const locSelect = document.getElementById("localityFilterSelect");
  if (locSelect) locSelect.addEventListener("change", renderLeadsTable);

  const sortSelect = document.getElementById("sortSelect");
  if (sortSelect) sortSelect.addEventListener("change", renderLeadsTable);

  // Copy Suggested Reply on Detail Page
  const copyReplyBtn = document.getElementById("detailCopyReplyBtn");
  if (copyReplyBtn) {
    copyReplyBtn.addEventListener("click", () => {
      const text = document.getElementById("detailAiSuggestedReply").textContent;
      navigator.clipboard.writeText(text).then(() => {
        showToast("Suggested reply copied to clipboard!");
      });
    });
  }

  // Regenerate Suggested Customer Reply on Detail Page
  const regenReplyBtn = document.getElementById("detailRegenerateReplyBtn");
  const suggestedReplyEl = document.getElementById("detailAiSuggestedReply");
  if (regenReplyBtn && suggestedReplyEl) {
    regenReplyBtn.addEventListener("click", async () => {
      const lead = leads.find(l => l.id === currentLeadId) || leads[0];
      if (!lead) return;

      const currentText = (suggestedReplyEl.textContent || "").trim();
      const leadKey = lead.id || "default";
      leadRegenerateCounts[leadKey] = (leadRegenerateCounts[leadKey] || 0) + 1;
      const variation = leadRegenerateCounts[leadKey];

      // Enter loading state
      regenReplyBtn.disabled = true;
      regenReplyBtn.classList.add("is-regenerating");
      const labelSpan = regenReplyBtn.querySelector(".regen-label");
      const originalLabel = labelSpan ? labelSpan.textContent : "Regenerate Reply";
      if (labelSpan) labelSpan.textContent = "Regenerating...";

      try {
        let newReply = null;

        // 1. Try Live Gemini Backend API
        try {
          const res = await fetch(`/api/leads/${lead.id}/regenerate-reply`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ current_reply: currentText, variation: variation })
          });
          if (res.ok) {
            const data = await res.json();
            if (data && data.success && data.reply) {
              newReply = data.reply.trim();
            }
          }
        } catch (apiErr) {
          console.warn("Backend regenerate endpoint unavailable, using local generator:", apiErr);
        }

        // 2. Client-side heuristic fallback if offline/mock
        if (!newReply) {
          newReply = generateClientAlternativeReply(lead, variation, currentText);
        }

        // 3. Update DOM with smooth fade animation
        suggestedReplyEl.textContent = newReply;
        suggestedReplyEl.classList.remove("reply-updated");
        void suggestedReplyEl.offsetWidth; // Force reflow
        suggestedReplyEl.classList.add("reply-updated");

        // 4. Update memory state
        if (!lead.ai_analysis) lead.ai_analysis = {};
        lead.ai_analysis.suggested_response = newReply;

        showToast("✨ New suggested reply regenerated!");
      } catch (err) {
        console.error("Failed to regenerate reply:", err);
        showToast("Error regenerating reply. Please try again.");
      } finally {
        regenReplyBtn.disabled = false;
        regenReplyBtn.classList.remove("is-regenerating");
        if (labelSpan) labelSpan.textContent = originalLabel;
      }
    });
  }

  // Generate Follow-Up Message in Detail View
  const genFollowupBtn = document.getElementById("detailGenFollowupBtn");
  const followupBox = document.getElementById("detailFollowupBox");
  if (genFollowupBtn && followupBox) {
    genFollowupBtn.addEventListener("click", () => {
      followupBox.style.display = "block";
      showToast("Personalized follow-up message prepared!");
    });
  }

  const closeFollowup = document.getElementById("closeDetailFollowupBtn");
  if (closeFollowup) {
    closeFollowup.addEventListener("click", () => {
      followupBox.style.display = "none";
    });
  }

  const copyFollowupTextBtn = document.getElementById("detailCopyFollowupTextBtn");
  if (copyFollowupTextBtn) {
    copyFollowupTextBtn.addEventListener("click", () => {
      const msg = document.getElementById("detailFollowupText").value;
      navigator.clipboard.writeText(msg).then(() => {
        showToast("WhatsApp follow-up text copied!");
      });
    });
  }

  const markSentBtn = document.getElementById("detailMarkFollowupSentBtn");
  if (markSentBtn) {
    markSentBtn.addEventListener("click", () => {
      const lead = leads.find(l => l.id === currentLeadId);
      if (lead && lead.followup) {
        lead.followup.status = "completed";
        lead.followup.due = "Completed Today";
        document.getElementById("detailFollowupDue").textContent = "Completed Today";
        document.getElementById("detailFollowupDue").style.color = "var(--emerald-600)";
        followupBox.style.display = "none";
        updateGlobalMetrics();
        showToast("Follow-up marked as completed!");
      }
    });
  }

  const logCallBtn = document.getElementById("detailLogCallBtn");
  if (logCallBtn) {
    logCallBtn.addEventListener("click", () => {
      showToast("Touchpoint logged: 'Spoke with customer, verified timeline & requirements'");
    });
  }

  async function askLeadCopilot(lead, question) {
    if (!lead.chat_history) lead.chat_history = [];
    lead.chat_history.push({ sender: "user", text: question });
    renderDetailChatThread(lead);

    try {
      const res = await fetch(`/api/leads/${lead.id}/copilot`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: question })
      });
      if (res.ok) {
        const data = await res.json();
        if (data.success && data.reply) {
          lead.chat_history.push({ sender: "assistant", text: data.reply });
          renderDetailChatThread(lead);
          return;
        }
      }
    } catch (err) {
      console.log("[Copilot API] Offline, using local copilot:", err);
    }

    setTimeout(() => {
      const reply = generateDetailGroundedReply(lead, question);
      lead.chat_history.push({ sender: "assistant", text: reply });
      renderDetailChatThread(lead);
    }, 350);
  }

  // Detail Chat Grounded Copilot
  const chatForm = document.getElementById("detailChatForm");
  const chatInput = document.getElementById("detailChatInput");
  if (chatForm && chatInput) {
    chatForm.addEventListener("submit", (e) => {
      e.preventDefault();
      const q = chatInput.value.trim();
      if (!q) return;

      const lead = leads.find(l => l.id === currentLeadId);
      if (!lead) return;

      chatInput.value = "";
      askLeadCopilot(lead, q);
    });
  }

  // Copilot Prompt Chips
  document.querySelectorAll(".chip-prompt").forEach(chip => {
    chip.addEventListener("click", () => {
      const lead = leads.find(l => l.id === currentLeadId);
      if (!lead) return;
      const q = chip.dataset.query;
      askLeadCopilot(lead, q);
    });
  });

  // Modal Controls
  const openModalBtn = document.getElementById("sidebarNewLeadBtn");
  const modal = document.getElementById("leadIntakeModal");
  const closeModalBtn = document.getElementById("closeIntakeModalBtn");
  const cancelModalBtn = document.getElementById("cancelIntakeModalBtn");

  if (openModalBtn && modal) {
    openModalBtn.addEventListener("click", () => {
      switchIntakeMode("manual");
      modal.style.display = "flex";
    });
  }
  if (closeModalBtn && modal) {
    closeModalBtn.addEventListener("click", () => { modal.style.display = "none"; });
  }
  if (cancelModalBtn && modal) {
    cancelModalBtn.addEventListener("click", () => { modal.style.display = "none"; });
  }

  // Modal Presets
  document.querySelectorAll(".btn-preset").forEach(btn => {
    btn.addEventListener("click", () => {
      const p = btn.dataset.preset;
      const phoneInput = document.getElementById("inputPhone");
      if (phoneInput) phoneInput.classList.remove("input-error");

      if (p === "hot_relocation") {
        document.getElementById("inputName").value = "Kavita Rao";
        if (phoneInput) phoneInput.value = "+91 98765 43210";
        document.getElementById("inputLocation").value = "Whitefield";
        document.getElementById("inputReq").value = "3BHK apartment, ready to move";
        document.getElementById("inputBudget").value = "1.5 Cr";
        document.getElementById("inputTimeline").value = "Within 1 month";
        document.getElementById("inputMessage").value = "Relocating from Hyderabad this month for job at ITPL. HDFC loan sanctioned for 1.2 Cr. Can we inspect units this Saturday?";
      } else if (p === "warm_unrealistic") {
        document.getElementById("inputName").value = "Manish Tiwari";
        if (phoneInput) phoneInput.value = "+91 98112 34567";
        document.getElementById("inputLocation").value = "Whitefield";
        document.getElementById("inputReq").value = "3BHK Villa";
        document.getElementById("inputBudget").value = "50 L";
        document.getElementById("inputTimeline").value = "Within 1 month";
        document.getElementById("inputMessage").value = "Need luxury 3BHK villa urgently in Whitefield with clubhouse. Budget 50 Lakhs cash.";
      } else if (p === "cold_price") {
        document.getElementById("inputName").value = "Siddharth B";
        if (phoneInput) phoneInput.value = "+91 99001 23456";
        document.getElementById("inputLocation").value = "Bangalore";
        document.getElementById("inputReq").value = "Apartment";
        document.getElementById("inputBudget").value = "";
        document.getElementById("inputTimeline").value = "Not decided";
        document.getElementById("inputMessage").value = "price list details please?";
      }
    });
  });

  // Modal Submit
  const intakeForm = document.getElementById("leadIntakeForm");
  const phoneInputEl = document.getElementById("inputPhone");
  if (phoneInputEl) {
    phoneInputEl.addEventListener("input", () => {
      phoneInputEl.classList.remove("input-error");
    });
  }

  if (intakeForm) {
    intakeForm.addEventListener("submit", async (e) => {
      e.preventDefault();

      const name = document.getElementById("inputName").value.trim();
      const phoneInput = document.getElementById("inputPhone");
      const rawPhone = phoneInput ? phoneInput.value.trim() : "";
      const loc = document.getElementById("inputLocation").value.trim();
      const req = document.getElementById("inputReq").value.trim();
      const budget = document.getElementById("inputBudget").value.trim();
      const timeline = document.getElementById("inputTimeline").value;
      const msg = document.getElementById("inputMessage").value.trim();

      // Mandatory Phone validation with country code support
      const phoneCheck = validatePhoneNumber(rawPhone);
      if (!phoneCheck.valid) {
        if (phoneInput) phoneInput.classList.add("input-error");
        showToast(phoneCheck.message);
        if (phoneInput) phoneInput.focus();
        return;
      }
      if (phoneInput) phoneInput.classList.remove("input-error");
      const phone = normalizePhoneNumber(rawPhone);

      const submitBtn = document.getElementById("submitLeadBtn");
      const origText = submitBtn.innerHTML;
      submitBtn.innerHTML = "<span>Analyzing & Qualifying...</span>";
      submitBtn.disabled = true;

      // 1. Try Live Flask API
      try {
        const res = await fetch("/api/leads", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            name,
            phone,
            location: loc,
            property_requirement: req,
            budget,
            timeline,
            message: msg
          })
        });

        if (res.ok) {
          const data = await res.json();
          if (data.success && data.lead) {
            leads.unshift(data.lead);
            modal.style.display = "none";
            intakeForm.reset();
            submitBtn.innerHTML = origText;
            submitBtn.disabled = false;
            updateGlobalMetrics();
            showToast(`Lead '${name}' classified as ${data.lead.priority} (${data.lead.score}/100)!`);
            openLeadDetail(data.lead.id);
            return;
          }
        }
      } catch (err) {
        console.log("[Intake API] Offline fallback:", err);
      }

      // 2. Client-side fallback
      setTimeout(() => {
        const newLead = createEvaluatedLead(name, phone, loc, req, budget, timeline, msg);
        leads.unshift(newLead);

        modal.style.display = "none";
        intakeForm.reset();
        submitBtn.innerHTML = origText;
        submitBtn.disabled = false;

        updateGlobalMetrics();
        showToast(`Lead '${name}' classified as ${newLead.priority} (${newLead.score}/100)!`);

        // Open the newly created lead dossier directly!
        openLeadDetail(newLead.id);
      }, 500);
    });
  }
}

function isHinglishQuery(text) {
  if (!text) return false;
  // Check Devanagari Unicode
  if (/[\u0900-\u097F]/.test(text)) return true;

  const hinglishTokens = [
    /\bke\b/i, /\bki\b/i, /\bka\b/i, /\bko\b/i, /\bmein\b/i, /\bse\b/i, /\bpe\b/i, /\bpar\b/i,
    /\bmai\b/i, /\bmain\b/i, /\bmujhe\b/i, /\bmera\b/i, /\bmeri\b/i, /\bmere\b/i, /\bhum\b/i, /\bhamara\b/i,
    /\bbatao\b/i, /\bbataiye\b/i, /\bbata\b/i, /\bbtao\b/i,
    /\bkya\b/i, /\bky\b/i, /\bkyaa\b/i, /\bkyun\b/i, /\bkyu\b/i, /\bhai\b/i, /\bhain\b/i, /\btha\b/i, /\bthe\b/i, /\bthi\b/i,
    /\bkaise\b/i, /\bkese\b/i, /\bkab\b/i, /\bkaha\b/i, /\bkahan\b/i,
    /\bkaro\b/i, /\bkare\b/i, /\bkarein\b/i, /\bkarna\b/i, /\bkaru\b/i, /\bkaroon\b/i, /\bchahiye\b/i,
    /\bye\b/i, /\byeh\b/i, /\bwo\b/i, /\bwoh\b/i,
    /\biska\b/i, /\biski\b/i, /\biske\b/i, /\bunka\b/i, /\bunki\b/i, /\bunke\b/i, /\binke\b/i, /\binka\b/i,
    /\busko\b/i, /\bisko\b/i, /\bunko\b/i,
    /\bbolo\b/i, /\bbolna\b/i, /\bbolu\b/i, /\bbole\b/i, /\bboliye\b/i, /\babolu\b/i,
    /\bbhej\b/i, /\bbhejo\b/i, /\bkitna\b/i, /\bkitne\b/i, /\bkitni\b/i,
    /\baccha\b/i, /\bachha\b/i, /\btheek\b/i, /\bsamjhao\b/i, /\bkuch\b/i, /\bkaisa\b/i, /\bkaisi\b/i,
    /\bnahi\b/i, /\bnhi\b/i, /\bhaan\b/i, /\bdikkat\b/i, /\bpaise\b/i, /\brupaye\b/i, /\bbaat\b/i,
    /\btoh\b/i, /\bbhi\b/i, /\bhoga\b/i, /\bhogi\b/i, /\bhoge\b/i
  ];

  return hinglishTokens.some(rx => rx.test(text));
}

function generateDetailGroundedReply(lead, query) {
  const q = query.toLowerCase();
  const isHinglish = isHinglishQuery(query);
  const firstName = (lead.name || 'Customer').split(' ')[0];
  const loc = lead.location || 'Bangalore';
  const req = lead.property_requirement || 'Property';
  const budget = lead.budget || 'Open';

  // -------------------------------------------------------------
  // HINGLISH RESPONSE GENERATOR (Concise, Professional & Natural)
  // -------------------------------------------------------------
  if (isHinglish) {
    if (q.includes("pitch") || q.includes("call") || q.includes("baat") || q.includes("bol") || q.includes("samjha") || q.includes("emphasize") || q.includes("abolu") || q.includes("kya")) {
      return `🗣️ **Call Script:**\n` +
             `*"Namaste ${firstName} ji! ${loc} mein aapke ₹${budget} budget ke mutabiq verified ready-to-move ${req} units shortlist kiye hain. Kya hum Saturday ko site visit confirm karein?"*\n\n` +
             `📋 **Key Points:**\n` +
             `• **Matched Inventory**: ${loc} mein ${req} ready options highlight karein.\n` +
             `• **Budget**: ₹${budget} pricing transparently discuss karein.\n` +
             `• **Closing Goal**: Saturday site visit ka slot lock karein.`;
    }

    if (q.includes("objection") || q.includes("dikkat") || q.includes("problem") || q.includes("issue") || q.includes("concern") || q.includes("rok")) {
      const objs = (lead.ai_analysis && lead.ai_analysis.objections && lead.ai_analysis.objections.length)
        ? lead.ai_analysis.objections
        : ["Documentation & pricing transparency"];
      return `**${lead.name}** ke key concerns:\n` +
             `• **${objs.join("\n• ")}**\n\n` +
             `💡 **Action**: Call par pehle verified RERA/OC proof aur clear cost-sheet share karein.`;
    }

    if (q.includes("budget") || q.includes("paise") || q.includes("price") || q.includes("cost") || q.includes("kitna")) {
      return `• **Budget**: ₹${budget}\n` +
             `• **Readiness Score**: ${(lead.breakdown && lead.breakdown.budget) ? `${lead.breakdown.budget.score}/${lead.breakdown.budget.max}` : 'Verified'}\n` +
             `• **Status**: ${loc} mein ${req} requirements ke sath aligned hai.`;
    }

    if (q.includes("timeline") || q.includes("kab") || q.includes("urgent") || q.includes("urgency") || q.includes("shift")) {
      return `• **Buying Timeline**: ${lead.timeline || 'Not specified'}\n` +
             `• **Urgency**: ${lead.urgency_label || 'Standard'}\n` +
             `• **Next Step**: ${(lead.ai_analysis && lead.ai_analysis.next_action) || 'Call and confirm inspection'}`;
    }

    if (q.includes("message") || q.includes("reply") || q.includes("whatsapp") || q.includes("likhu") || q.includes("bhej") || q.includes("draft")) {
      return `📱 **WhatsApp Template:**\n` +
             `*"Namaste ${firstName} ji, aapke ₹${budget} budget mein ${loc} ke verified ${req} units available hain. Kya hum Saturday ko walkthrough schedule karein?"*`;
    }

    // Default concise overview
    return `**${lead.name}** (${lead.priority} · ${lead.score}/100):\n` +
           `• **Need**: ${loc} mein ${req}\n` +
           `• **Budget**: ₹${budget} | **Timeline**: ${lead.timeline || 'Immediate'}\n` +
           `• **Next Action**: ${(lead.ai_analysis && lead.ai_analysis.next_action) || 'Call and secure site visit'}`;
  }

  // -------------------------------------------------------------
  // ENGLISH RESPONSE GENERATOR (Concise, Professional & Bulleted)
  // -------------------------------------------------------------
  if (q.includes("emphasize") || q.includes("call") || q.includes("pitch") || q.includes("say") || q.includes("speak")) {
    return `🗣️ **Call Script:**\n` +
           `*"Hi ${firstName}, we've shortlisted verified ready-to-move ${req} units in ${loc} matching your ₹${budget} budget. Can we confirm a walkthrough this Saturday?"*\n\n` +
           `📋 **Key Points:**\n` +
           `• Highlight verified inventory matching ${req} in ${loc}.\n` +
           `• Reaffirm budget alignment of ₹${budget}.\n` +
           `• Lock in a firm Saturday site visit slot.`;
  }

  if (q.includes("objection") || q.includes("handle") || q.includes("concern")) {
    const objs = (lead.ai_analysis && lead.ai_analysis.objections && lead.ai_analysis.objections.length)
      ? lead.ai_analysis.objections
      : ["Price verification and possession timeline"];
    return `**Active Concerns Identified:**\n` +
           `• **${objs.join("\n• ")}**\n\n` +
           `💡 **Strategy**: Acknowledge early and present verified OC/RERA documentation.`;
  }

  if (q.includes("assertive") || q.includes("urgent") || q.includes("rewrite")) {
    return `📱 **Assertive WhatsApp Message:**\n` +
           `*"Hi ${firstName}, we have 2 ready units matching your ${req} criteria in ${loc} under ₹${budget}. Due to high weekend demand, I can hold one for your inspection this Saturday noon. Please confirm by 5 PM."*`;
  }

  if (q.includes("budget") || q.includes("price") || q.includes("cost")) {
    return `• **Budget**: ₹${budget}\n` +
           `• **Budget Score**: ${(lead.breakdown && lead.breakdown.budget) ? `${lead.breakdown.budget.score}/${lead.breakdown.budget.max}` : 'Verified'}\n` +
           `• **Status**: Fits verified inventory in ${loc}.`;
  }

  return `**${lead.name}** (${lead.priority} · ${lead.score}/100):\n` +
         `• **Need**: ${req} in ${loc}\n` +
         `• **Budget**: ₹${budget} | **Timeline**: ${lead.timeline || 'Immediate'}\n` +
         `• **Next Action**: ${(lead.ai_analysis && lead.ai_analysis.next_action) || 'Contact immediately'}`;
}

// -------------------------------------------------------------
// Client Alternative Reply Generator for Suggested Customer Reply
// -------------------------------------------------------------
const leadRegenerateCounts = {};

function generateClientAlternativeReply(lead, variation, currentText) {
  const firstName = (lead.name || "Customer").split(" ")[0];
  const loc = lead.location || "Bangalore";
  const req = lead.property_requirement || "property";
  const budget = lead.budget || "your budget";
  const timeline = lead.timeline || "soon";
  const isHinglish = isHinglishQuery(lead.message || "") || isHinglishQuery(currentText || "");

  if (isHinglish) {
    const hinglishVariations = [
      `Hi ${firstName}, ${loc} mein aapki requirement ke mutabiq ${req} ki prime ready units shortlist ki hain. Kya hum iss Saturday 11:30 AM site visit plan karein? Main convenience ke hisaab se timing fix kar deta hoon.`,
      `Hi ${firstName}! ${budget} ke budget mein ${loc} ke 2 best verified ready-to-move projects available hain jinka OC aur clear title ready hai. Aapko detailed cost sheet aur floor plans WhatsApp kar doon?`,
      `Hi ${firstName}, thank you for reaching out! ${req} mein specific facing ya floor preference hai? Aaj evening 5 baje 5-minute quick call par connect karein taaki exact inventory options share kar sakun?`,
      `Hi ${firstName}, ${loc} mein iss budget aur configuration ki premium units tezi se book ho rahi hain. Weekend ke pehle shortlist lock kar lete hain—kal afternoon aapke paas 10 minute ka waqt hoga baat karne ke liye?`,
      `Hi ${firstName}, Bangalore property search mein swagat hai! ${req} ke verified options ready hain jo aapke ${timeline} timeline se perfectly align hote hain. Batayein kab call schedule karein?`
    ];
    const candidates = hinglishVariations.filter(v => v.trim() !== (currentText || "").trim());
    return (candidates.length ? candidates[(variation - 1) % candidates.length] : hinglishVariations[0]);
  } else {
    const englishVariations = [
      `Hi ${firstName}, I have identified 2 ready-to-move ${req} options in ${loc} that match your exact criteria. Could we schedule a walkthrough this Saturday morning to view the actual units?`,
      `Hi ${firstName}, thank you for reaching out! We have premium RERA-verified units in ${loc} that fit comfortably within your ₹${budget} budget with complete OC ready. May I share the verified cost sheets and floor plans over WhatsApp?`,
      `Hi ${firstName}, to ensure we only share the most relevant ${req} units in ${loc}, do you have specific preferences regarding floor or facing? Let me know a convenient 5-minute window today to align.`,
      `Hi ${firstName}, verified inventory for ${req} in ${loc} is moving rapidly this month. I would like to block the top 2 units for you before the weekend rush—would a brief 10-minute call today at 4 PM work?`,
      `Hi ${firstName}, welcome to our verified property network in ${loc}! I have handpicked options tailored to your ${timeline} move-in plan and ₹${budget} budget. Let me know when you would like to connect.`
    ];
    const candidates = englishVariations.filter(v => v.trim() !== (currentText || "").trim());
    return (candidates.length ? candidates[(variation - 1) % candidates.length] : englishVariations[0]);
  }
}

// -------------------------------------------------------------
// Phone Number Validation & Normalization
// -------------------------------------------------------------
function validatePhoneNumber(rawPhone) {
  if (!rawPhone || typeof rawPhone !== "string") {
    return { valid: false, message: "Phone number is mandatory." };
  }
  const trimmed = rawPhone.trim();
  if (!trimmed) {
    return { valid: false, message: "Phone number is mandatory." };
  }
  // Allow leading +, digits, spaces, hyphens, and parentheses
  const validPhoneRegex = /^(\+?\d{1,4}[-.\s]?)?(\(?\d{2,5}\)?[-.\s]?)?\d{3,5}[-.\s]?\d{3,5}$/;
  const digits = trimmed.replace(/\D/g, "");
  if (!validPhoneRegex.test(trimmed) || digits.length < 10 || digits.length > 15) {
    return {
      valid: false,
      message: "Please enter a valid phone number with country code (e.g., +91 98765 43210 or 10-digit number)."
    };
  }
  return { valid: true, clean: trimmed };
}

function normalizePhoneNumber(rawPhone) {
  if (!rawPhone) return "";
  const trimmed = rawPhone.trim();
  const digits = trimmed.replace(/\D/g, "");
  // If user entered exactly 10 digits without country code, prefix standard +91
  if (!trimmed.startsWith("+") && digits.length === 10) {
    return `+91 ${digits.slice(0, 5)} ${digits.slice(5)}`;
  }
  return trimmed;
}

function createEvaluatedLead(name, phone, loc, req, budget, timeline, msg) {
  const isUrgent = timeline.includes("1 month") || msg.toLowerCase().includes("urgent") || msg.toLowerCase().includes("relocating");
  const isVillaLow = req.toLowerCase().includes("villa") && (parseFloat(budget) || 0) < 100;
  const isMinimal = msg.split(" ").length <= 4;

  let priority = "Warm";
  let score = 65;
  let urgency = "Follow up in 2 days";

  if (isVillaLow) {
    priority = "Warm";
    score = 48;
    urgency = "Call to reset expectations";
  } else if (isMinimal && !budget) {
    priority = "Cold";
    score = 15;
    urgency = "Automated nurture";
  } else if (isUrgent && budget) {
    priority = "Hot";
    score = 88;
    urgency = "Call within 15 min";
  }

  return {
    id: "L" + (leads.length + 1).toString().padStart(2, "0"),
    name: name,
    phone: phone || "+91 Unspecified",
    location: loc,
    property_requirement: req,
    budget: budget,
    timeline: timeline,
    urgency_label: urgency,
    message: msg,
    priority: priority,
    score: score,
    breakdown: {
      timeline: { label: "Buying Timeline", score: isUrgent ? 19 : 11, max: 20 },
      budget: { label: "Budget Readiness", score: isVillaLow ? 3 : 18, max: 20 },
      intent: { label: "Purchase Intent", score: isUrgent ? 18 : 12, max: 20 },
      requirement: { label: "Property Specificity", score: 12, max: 15 },
      engagement: { label: "Inquiry Depth", score: 6, max: 10 },
      readiness: { label: "Decision Readiness", score: isUrgent ? 12 : 5, max: 15 }
    },
    signals: [
      `Inquired for ${loc}`,
      `Stated budget ₹${budget || 'Unspecified'}`,
      isUrgent ? "Urgent timeframe detected" : "Standard exploratory inquiry"
    ],
    flags: isVillaLow ? ["UNREALISTIC_BUDGET"] : [],
    ai_analysis: {
      summary: `${name} is looking for a ${req} in ${loc} with a budget of ₹${budget || 'open'}.`,
      intent: isUrgent ? "High buying urgency with active timeline." : "Exploring property options.",
      requirements: `${req}, ${loc}, ₹${budget || 'unspecified'}.`,
      objections: isVillaLow ? ["Budget is far below market reality for villas"] : ["Needs price list and floor plans"],
      next_action: isUrgent ? "Contact immediately to confirm site visit" : "Share brochure and follow up in 48 hours",
      suggested_response: `Hi ${name.split(' ')[0]}, thank you for reaching out regarding our properties in ${loc}! We have options matching your ${req} criteria. When is a good time for a quick call?`
    },
    followup: {
      cadence: priority === "Hot" ? "Every 24 hours" : "Every 3 days",
      due: priority === "Hot" ? "Today by 4:00 PM" : "In 2 days",
      status: "due",
      goal: `Qualify ${req} requirements and confirm visit`,
      window: "Afternoon",
      template: `Hi ${name.split(' ')[0]}, following up on your inquiry for ${loc}. Let me know if you would like me to share the floor plans and price sheet on WhatsApp.`
    },
    chat_history: [
      { sender: "assistant", text: `Lead **${name}** added to pipeline. Evaluated as **${priority} (${score}/100)**. Ask me anything to prepare your outreach!` }
    ]
  };
}

function showToast(message) {
  const toastContainer = document.getElementById("toastContainer");
  const toast = document.createElement("div");
  toast.className = "toast";
  toast.innerHTML = `<span>🌱</span> <span>${message}</span>`;
  toastContainer.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transform = "translateY(10px)";
    toast.style.transition = "all 0.2s ease";
    setTimeout(() => toast.remove(), 200);
  }, 2600);
}



// -------------------------------------------------------------
// Priority Status Distribution: Dynamic Donut Chart & Metrics
// -------------------------------------------------------------
function parseLeadBudgetCrores(budgetString) {
  if (!budgetString) return 0;
  const str = String(budgetString).toLowerCase().replace(/₹|,/g, "").trim();
  const numMatch = str.match(/[\d.]+/);
  if (!numMatch) return 0;
  const val = parseFloat(numMatch[0]);
  if (isNaN(val)) return 0;
  if (str.includes("cr")) return val;
  if (str.includes("l") || str.includes("lac") || str.includes("lakh")) return val / 100;
  if (str.includes("k")) return val / 100000;
  if (val > 100000) return val / 10000000;
  return val;
}

function formatPipelineVal(valInCrores) {
  if (!valInCrores || valInCrores <= 0) return "₹0";
  if (valInCrores >= 1) return `₹${valInCrores.toFixed(1)} Cr`;
  const lakhs = Math.round(valInCrores * 100);
  return `₹${lakhs} L`;
}

function updatePriorityDistribution() {
  const total = leads.length;
  const hotLeads = leads.filter(l => (l.priority || "").toLowerCase() === "hot");
  const warmLeads = leads.filter(l => (l.priority || "").toLowerCase() === "warm");
  const coldLeads = leads.filter(l => (l.priority || "").toLowerCase() === "cold");

  const hotCount = hotLeads.length;
  const warmCount = warmLeads.length;
  const coldCount = coldLeads.length;

  const hotPct = total > 0 ? Math.round((hotCount / total) * 100) : 0;
  const warmPct = total > 0 ? Math.round((warmCount / total) * 100) : 0;
  const coldPct = total > 0 ? Math.max(0, 100 - hotPct - warmPct) : 0;

  const hotVal = hotLeads.reduce((sum, l) => sum + parseLeadBudgetCrores(l.budget), 0);
  const warmVal = warmLeads.reduce((sum, l) => sum + parseLeadBudgetCrores(l.budget), 0);
  const coldVal = coldLeads.reduce((sum, l) => sum + parseLeadBudgetCrores(l.budget), 0);

  // Update center text
  const countEl = document.getElementById("donutCenterCount");
  const labelEl = document.getElementById("donutCenterLabel");
  if (countEl) {
    countEl.textContent = total;
    countEl.setAttribute("fill", "#000000");
  }
  if (labelEl) {
    labelEl.textContent = "TOTAL LEADS";
    labelEl.setAttribute("fill", "#333333");
  }

  // Circumference of r=60 is 2 * PI * 60 = 376.99
  const C = 376.99;
  const sliceHot = document.getElementById("donutSliceHot");
  const sliceWarm = document.getElementById("donutSliceWarm");
  const sliceCold = document.getElementById("donutSliceCold");

  if (total === 0) {
    if (sliceHot) sliceHot.setAttribute("stroke-dasharray", `0 ${C}`);
    if (sliceWarm) sliceWarm.setAttribute("stroke-dasharray", `0 ${C}`);
    if (sliceCold) sliceCold.setAttribute("stroke-dasharray", `0 ${C}`);
  } else {
    const hotLen = (hotCount / total) * C;
    const warmLen = (warmCount / total) * C;
    const coldLen = (coldCount / total) * C;

    if (sliceHot) {
      sliceHot.setAttribute("stroke-dasharray", `${hotLen.toFixed(1)} ${(C - hotLen).toFixed(1)}`);
      sliceHot.setAttribute("stroke-dashoffset", "0");
      const title = sliceHot.querySelector("title");
      if (title) title.textContent = `Hot Leads: ${hotCount} (${hotPct}%)`;
    }
    if (sliceWarm) {
      sliceWarm.setAttribute("stroke-dasharray", `${warmLen.toFixed(1)} ${(C - warmLen).toFixed(1)}`);
      sliceWarm.setAttribute("stroke-dashoffset", `-${hotLen.toFixed(1)}`);
      const title = sliceWarm.querySelector("title");
      if (title) title.textContent = `Warm Leads: ${warmCount} (${warmPct}%)`;
    }
    if (sliceCold) {
      sliceCold.setAttribute("stroke-dasharray", `${coldLen.toFixed(1)} ${(C - coldLen).toFixed(1)}`);
      sliceCold.setAttribute("stroke-dashoffset", `-${(hotLen + warmLen).toFixed(1)}`);
      const title = sliceCold.querySelector("title");
      if (title) title.textContent = `Cold Leads: ${coldCount} (${coldPct}%)`;
    }
  }

  // Update right-hand metric list
  const elHotPct = document.getElementById("distHotPct");
  if (elHotPct) elHotPct.textContent = `${hotPct}% (${hotCount} lead${hotCount === 1 ? "" : "s"})`;
  const elHotVal = document.getElementById("distHotVal");
  if (elHotVal) elHotVal.textContent = `${formatPipelineVal(hotVal)} Pipeline Value · Call within 24h`;

  const elWarmPct = document.getElementById("distWarmPct");
  if (elWarmPct) elWarmPct.textContent = `${warmPct}% (${warmCount} lead${warmCount === 1 ? "" : "s"})`;
  const elWarmVal = document.getElementById("distWarmVal");
  if (elWarmVal) elWarmVal.textContent = `${formatPipelineVal(warmVal)} Pipeline Value · 48-72h cadence`;

  const elColdPct = document.getElementById("distColdPct");
  if (elColdPct) elColdPct.textContent = `${coldPct}% (${coldCount} lead${coldCount === 1 ? "" : "s"})`;
  const elColdVal = document.getElementById("distColdVal");
  if (elColdVal) elColdVal.textContent = `${formatPipelineVal(coldVal)} Pipeline Value · Automated nurture`;
}

// -------------------------------------------------------------
// Donut Chart Hover: Dynamic slice counts & colors
// -------------------------------------------------------------
function setupDonutHover() {
  const slices = document.querySelectorAll(".donut-arc-slice");
  const countEl = document.getElementById("donutCenterCount");
  const labelEl = document.getElementById("donutCenterLabel");

  if (!countEl || !labelEl) return;

  slices.forEach(slice => {
    if (slice._hasDonutHover) return;
    slice._hasDonutHover = true;

    slice.addEventListener("mouseenter", () => {
      const key = (slice.dataset.key || "").toLowerCase();
      const filtered = leads.filter(l => (l.priority || "").toLowerCase() === key);
      const colors = { hot: "#dc2626", warm: "#d97706", cold: "#2563eb" };

      countEl.textContent = filtered.length;
      countEl.setAttribute("fill", colors[key] || "#000000");
      labelEl.textContent = key.toUpperCase();
      labelEl.setAttribute("fill", colors[key] || "#333333");
    });

    slice.addEventListener("mouseleave", () => {
      countEl.textContent = leads.length;
      countEl.setAttribute("fill", "#000000");
      labelEl.textContent = "TOTAL LEADS";
      labelEl.setAttribute("fill", "#333333");
    });
  });
}

// -------------------------------------------------------------
// Draggable Resizer Panels for AI Chat & Intelligence
// -------------------------------------------------------------
function setupHorizontalResizer(config) {
  const {
    dividerId,
    targetPanelId,
    containerId,
    isRightTarget,
    minWidth = 260,
    maxRatio = 0.65,
    storageKey
  } = config;

  const dividerEl = document.getElementById(dividerId);
  const targetEl = document.getElementById(targetPanelId);
  const containerEl = document.getElementById(containerId);

  if (!dividerEl || !targetEl || !containerEl) return;

  // Restore saved width from localStorage if desktop view
  if (storageKey) {
    try {
      const saved = localStorage.getItem(storageKey);
      if (saved && window.innerWidth > 1180) {
        const savedW = parseInt(saved, 10);
        if (!isNaN(savedW) && savedW >= minWidth) {
          const containerRect = containerEl.getBoundingClientRect();
          const maxAllowed = containerRect.width > 0 ? (containerRect.width * maxRatio) : 600;
          const clampedW = Math.max(minWidth, Math.min(savedW, maxAllowed));
          targetEl.style.width = clampedW + "px";
          targetEl.style.flex = "0 0 " + clampedW + "px";
        }
      }
    } catch (e) {}
  }

  // Pointer drag handler (supports mouse & touch smoothly)
  dividerEl.addEventListener("pointerdown", (e) => {
    if (e.button !== 0 && e.pointerType === "mouse") return;
    e.preventDefault();

    dividerEl.classList.add("is-dragging");
    document.body.classList.add("is-resizing-x");

    const startX = e.clientX;
    const startWidth = targetEl.getBoundingClientRect().width;
    let animationFrameId = null;

    function onPointerMove(moveEvent) {
      if (animationFrameId) cancelAnimationFrame(animationFrameId);
      animationFrameId = requestAnimationFrame(() => {
        const containerRect = containerEl.getBoundingClientRect();
        const deltaX = moveEvent.clientX - startX;
        let newWidth = isRightTarget ? (startWidth - deltaX) : (startWidth + deltaX);

        // Keep other columns comfortably visible without horizontal container overflow
        const maxAvailable = Math.max(minWidth, containerRect.width - 320);
        const maxWidth = Math.min(containerRect.width * maxRatio, maxAvailable);
        newWidth = Math.max(minWidth, Math.min(newWidth, maxWidth));

        const roundedWidth = Math.round(newWidth);
        targetEl.style.width = roundedWidth + "px";
        targetEl.style.flex = "0 0 " + roundedWidth + "px";
      });
    }

    function onPointerUp() {
      if (animationFrameId) cancelAnimationFrame(animationFrameId);
      dividerEl.classList.remove("is-dragging");
      document.body.classList.remove("is-resizing-x");

      window.removeEventListener("pointermove", onPointerMove);
      window.removeEventListener("pointerup", onPointerUp);
      window.removeEventListener("pointercancel", onPointerUp);

      if (storageKey) {
        try {
          const finalWidth = Math.round(targetEl.getBoundingClientRect().width);
          localStorage.setItem(storageKey, finalWidth);
        } catch (e) {}
      }
    }

    window.addEventListener("pointermove", onPointerMove);
    window.addEventListener("pointerup", onPointerUp);
    window.addEventListener("pointercancel", onPointerUp);
  });
}

function setupVerticalResizer(config) {
  const {
    dividerId,
    targetCardId,
    isBottomTarget = true,
    minHeight = 200,
    maxHeight = 650,
    storageKey
  } = config;

  const dividerEl = document.getElementById(dividerId);
  const targetEl = document.getElementById(targetCardId);

  if (!dividerEl || !targetEl) return;

  // Restore saved height
  if (storageKey) {
    try {
      const saved = localStorage.getItem(storageKey);
      if (saved) {
        const savedH = parseInt(saved, 10);
        if (!isNaN(savedH) && savedH >= minHeight && savedH <= maxHeight) {
          targetEl.style.height = savedH + "px";
          targetEl.style.flex = "0 0 " + savedH + "px";
        }
      }
    } catch (e) {}
  }

  // Pointer drag handler
  dividerEl.addEventListener("pointerdown", (e) => {
    if (e.button !== 0 && e.pointerType === "mouse") return;
    e.preventDefault();

    dividerEl.classList.add("is-dragging");
    document.body.classList.add("is-resizing-y");

    const startY = e.clientY;
    const startHeight = targetEl.getBoundingClientRect().height;
    let animationFrameId = null;

    function onPointerMove(moveEvent) {
      if (animationFrameId) cancelAnimationFrame(animationFrameId);
      animationFrameId = requestAnimationFrame(() => {
        const deltaY = moveEvent.clientY - startY;
        let newHeight = isBottomTarget ? (startHeight - deltaY) : (startHeight + deltaY);
        newHeight = Math.max(minHeight, Math.min(newHeight, maxHeight));

        const roundedHeight = Math.round(newHeight);
        targetEl.style.height = roundedHeight + "px";
        targetEl.style.flex = "0 0 " + roundedHeight + "px";
      });
    }

    function onPointerUp() {
      if (animationFrameId) cancelAnimationFrame(animationFrameId);
      dividerEl.classList.remove("is-dragging");
      document.body.classList.remove("is-resizing-y");

      window.removeEventListener("pointermove", onPointerMove);
      window.removeEventListener("pointerup", onPointerUp);
      window.removeEventListener("pointercancel", onPointerUp);

      if (storageKey) {
        try {
          const finalHeight = Math.round(targetEl.getBoundingClientRect().height);
          localStorage.setItem(storageKey, finalHeight);
        } catch (e) {}
      }
    }

    window.addEventListener("pointermove", onPointerMove);
    window.addEventListener("pointerup", onPointerUp);
    window.addEventListener("pointercancel", onPointerUp);
  });
}

function setupResizablePanels() {
  // 1. Lead Detail: Sales Copilot Q&A (Right Panel) vs AI Intelligence (Center)
  setupHorizontalResizer({
    dividerId: "resizerDetailRight",
    targetPanelId: "detailColRight",
    containerId: "detailViewGrid",
    isRightTarget: true,
    minWidth: 260,
    maxRatio: 0.60,
    storageKey: "resizer_detail_right_w"
  });

  // 2. Lead Detail: Profile/Hero (Left Panel) vs AI Intelligence (Center)
  setupHorizontalResizer({
    dividerId: "resizerDetailLeft",
    targetPanelId: "detailColLeft",
    containerId: "detailViewGrid",
    isRightTarget: false,
    minWidth: 250,
    maxRatio: 0.45,
    storageKey: "resizer_detail_left_w"
  });

  // 3. Follow-Up Hub: Pending Actions (Left) vs AI Copilot Chat (Right Column)
  setupHorizontalResizer({
    dividerId: "resizerHubHorizontal",
    targetPanelId: "hubRightCol",
    containerId: "hubGrid",
    isRightTarget: true,
    minWidth: 300,
    maxRatio: 0.65,
    storageKey: "resizer_hub_right_w"
  });

  // 4. Follow-Up Hub: Vertical resize between Assistant Rules and AI Copilot Chat
  setupVerticalResizer({
    dividerId: "resizerHubVertical",
    targetCardId: "hubChatCard",
    isBottomTarget: true,
    minHeight: 200,
    maxHeight: 650,
    storageKey: "resizer_hub_chat_h"
  });
}

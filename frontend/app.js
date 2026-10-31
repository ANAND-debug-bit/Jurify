"use strict";

const API_PATH = "/api/v1/documents";
const MAX_FILE_BYTES = 5 * 1024 * 1024;
const MAX_TEXT_LENGTH = 20000;
const DISCLAIMER = "This is general information, not legal advice. Laws and circumstances vary - consult a qualified legal professional before making decisions.";
const SAMPLE_EN = `RESIDENTIAL RENTAL AGREEMENT

This Rental Agreement is made between Asha Mehta ("Landlord") and Rohan Shah ("Tenant") for the apartment at 14 Green Park, New Delhi.

1. TERM. The tenancy begins on 1 November 2026 and continues for eleven (11) months.

2. RENT. The Tenant shall pay INR 28,000 per month on or before the fifth day of each month. Late payment will incur a fee of INR 1,000 per day.

3. SECURITY DEPOSIT. The Tenant has paid a security deposit of INR 84,000. The Landlord may deduct any amount from the deposit for any reason, at the Landlord's sole discretion. The remaining balance, if any, will be returned within 90 days after the Tenant vacates.

4. REPAIRS. The Tenant is responsible for all repairs and maintenance, including structural repairs, plumbing, and electrical systems, regardless of cause or cost.

5. ACCESS. The Landlord may enter the apartment at any time without prior notice.

6. EARLY TERMINATION. The Tenant must give two months' written notice to end the tenancy early.`;
const SAMPLE_HI = `आवासीय किराया समझौता

यह किराया समझौता आशा मेहता ("मकान मालकिन") और रोहन शाह ("किरायेदार") के बीच 14 ग्रीन पार्क, नई दिल्ली स्थित फ्लैट के लिए किया गया है।

1. अवधि। किरायेदारी 1 नवंबर 2026 से शुरू होकर ग्यारह (11) महीने तक चलेगी।

2. किराया। किरायेदार हर महीने की पांच तारीख तक 28,000 रुपये किराया देगा। देर से भुगतान पर प्रति दिन 1,000 रुपये का शुल्क लगेगा।

3. सुरक्षा जमा। किरायेदार ने 84,000 रुपये जमा किए हैं। मकान मालकिन अपने विवेक से किसी भी कारण से जमा राशि काट सकती हैं। शेष राशि, यदि कोई हो, घर खाली करने के 90 दिनों के भीतर लौटाई जाएगी।

4. मरम्मत। किरायेदार सभी मरम्मत और रखरखाव के लिए जिम्मेदार होगा, जिसमें संरचनात्मक मरम्मत, पाइपलाइन और बिजली व्यवस्था शामिल है, कारण या लागत की परवाह किए बिना।

5. प्रवेश। मकान मालकिन बिना पूर्व सूचना के किसी भी समय फ्लैट में प्रवेश कर सकती हैं।

6. समय से पहले समाप्ति। किरायेदारी समय से पहले समाप्त करने के लिए किरायेदार को दो महीने का लिखित नोटिस देना होगा।`;

const MOCK_ANALYSIS_EN = {
  analysis_id: "demo-analysis-en-001",
  document_type: "Residential rental agreement",
  plain_summary: "This 11-month rental agreement sets a monthly rent of INR 28,000 and a deposit of INR 84,000. It also gives the landlord broad discretion over deposit deductions, puts all repairs on the tenant, and permits entry without notice. Review those terms carefully and clarify them in writing before signing.",
  key_clauses: [
    { title: "Agreement term", quote: "The tenancy begins on 1 November 2026 and continues for eleven (11) months.", explanation: "This describes the fixed length of the tenancy and its start date." },
    { title: "Monthly rent and late fee", quote: "The Tenant shall pay INR 28,000 per month on or before the fifth day of each month. Late payment will incur a fee of INR 1,000 per day.", explanation: "Rent is due by the fifth. The agreement also states a daily late-payment fee; ask how it is calculated." },
    { title: "Security deposit", quote: "The Landlord may deduct any amount from the deposit for any reason, at the Landlord's sole discretion.", explanation: "The wording gives the landlord wide discretion to deduct from the deposit, without listing specific reasons." },
    { title: "Repairs and access", quote: "The Tenant is responsible for all repairs and maintenance, including structural repairs, plumbing, and electrical systems, regardless of cause or cost.", explanation: "This places repair costs on the tenant even when the issue may not have been caused by them." }
  ],
  risk_flags: [
    { clause_title: "Security deposit deductions", quote: "The Landlord may deduct any amount from the deposit for any reason, at the Landlord's sole discretion.", risk_level: "high", reason: "There is no list of permitted deductions or clear requirement to provide an itemized explanation." },
    { clause_title: "All repairs assigned to tenant", quote: "The Tenant is responsible for all repairs and maintenance, including structural repairs, plumbing, and electrical systems, regardless of cause or cost.", risk_level: "high", reason: "This could make the tenant responsible for expensive repairs even if they did not cause the damage." },
    { clause_title: "Landlord entry without notice", quote: "The Landlord may enter the apartment at any time without prior notice.", risk_level: "medium", reason: "The clause does not set a notice period, permitted reason, or emergency-only exception for entry." }
  ],
  questions_to_ask: [
    "Can deposit deductions be limited to documented damage beyond normal wear and tear?",
    "Can the agreement distinguish tenant-caused damage from structural or routine repairs?",
    "Can the landlord provide advance notice before a non-emergency visit?",
    "How is the INR 1,000 daily late fee calculated, and is there a maximum?"
  ],
  language: "en",
  model: "gemma-4-26b-a4b-it",
  disclaimer: DISCLAIMER
};

const MOCK_ANALYSIS_HI = {
  analysis_id: "demo-analysis-hi-001",
  document_type: "आवासीय किराया समझौता",
  plain_summary: "यह 11 महीने का किराया समझौता 28,000 रुपये मासिक किराया और 84,000 रुपये सुरक्षा जमा तय करता है। इसमें मकान मालकिन को जमा राशि काटने का व्यापक अधिकार दिया गया है, सभी मरम्मत किरायेदार पर रखी गई हैं, और बिना सूचना प्रवेश की अनुमति है। हस्ताक्षर करने से पहले इन शर्तों को ध्यान से पढ़ें और लिखित में स्पष्ट करें।",
  key_clauses: [
    { title: "समझौते की अवधि", quote: "किरायेदारी 1 नवंबर 2026 से शुरू होकर ग्यारह (11) महीने तक चलेगी।", explanation: "इसमें किरायेदारी की अवधि और शुरू होने की तारीख बताई गई है।" },
    { title: "मासिक किराया और विलंब शुल्क", quote: "किरायेदार हर महीने की पांच तारीख तक 28,000 रुपये किराया देगा। देर से भुगतान पर प्रति दिन 1,000 रुपये का शुल्क लगेगा।", explanation: "किराया हर महीने की पांच तारीख तक देना है। देर से भुगतान के दैनिक शुल्क की गणना स्पष्ट करें।" },
    { title: "सुरक्षा जमा", quote: "मकान मालकिन अपने विवेक से किसी भी कारण से जमा राशि काट सकती हैं।", explanation: "इस भाषा में जमा राशि काटने के कारणों की कोई सूची नहीं दी गई है।" },
    { title: "मरम्मत और प्रवेश", quote: "किरायेदार सभी मरम्मत और रखरखाव के लिए जिम्मेदार होगा, जिसमें संरचनात्मक मरम्मत, पाइपलाइन और बिजली व्यवस्था शामिल है, कारण या लागत की परवाह किए बिना।", explanation: "इस शर्त के अनुसार किरायेदार को ऐसी मरम्मत का खर्च भी देना पड़ सकता है जो उसने नहीं कराई।" }
  ],
  risk_flags: [
    { clause_title: "सुरक्षा जमा में कटौती", quote: "मकान मालकिन अपने विवेक से किसी भी कारण से जमा राशि काट सकती हैं।", risk_level: "high", reason: "कटौती के मान्य कारणों की सूची या मदवार हिसाब देने की शर्त नहीं है।" },
    { clause_title: "सभी मरम्मत किरायेदार पर", quote: "किरायेदार सभी मरम्मत और रखरखाव के लिए जिम्मेदार होगा, जिसमें संरचनात्मक मरम्मत, पाइपलाइन और बिजली व्यवस्था शामिल है, कारण या लागत की परवाह किए बिना।", risk_level: "high", reason: "इससे किरायेदार को महंगी मरम्मत का खर्च देना पड़ सकता है, भले ही नुकसान उसने न किया हो।" },
    { clause_title: "बिना सूचना मकान में प्रवेश", quote: "मकान मालकिन बिना पूर्व सूचना के किसी भी समय फ्लैट में प्रवेश कर सकती हैं।", risk_level: "medium", reason: "इसमें सूचना की अवधि, प्रवेश का कारण या केवल आपातकाल में प्रवेश की सीमा नहीं बताई गई है।" }
  ],
  questions_to_ask: [
    "क्या जमा राशि में कटौती केवल दस्तावेज़ित नुकसान तक सीमित हो सकती है?",
    "क्या किरायेदार द्वारा किए गए नुकसान और सामान्य मरम्मत को अलग किया जा सकता है?",
    "क्या आपातकाल के अलावा आने से पहले मकान मालकिन सूचना देंगी?",
    "देर से भुगतान के 1,000 रुपये प्रतिदिन शुल्क की गणना कैसे होगी?"
  ],
  language: "hi",
  model: "gemma-4-26b-a4b-it",
  disclaimer: "यह सामान्य जानकारी है, कानूनी सलाह नहीं। कानून और परिस्थितियां अलग-अलग हो सकती हैं - निर्णय लेने से पहले किसी योग्य कानूनी पेशेवर से सलाह लें।"
};

const MOCK_ANSWERS = {
  "what is the notice period?": {
    answer: "The agreement says you must give two months' written notice to end the tenancy early. This answer is based on the early-termination clause in the document.",
    evidence_quotes: ["The Tenant must give two months' written notice to end the tenancy early."],
    confidence: "high"
  },
  "can the landlord keep my deposit?": {
    answer: "The document says the landlord may deduct any amount for any reason, at their sole discretion, and return any remaining balance within 90 days. The agreement does not specify an itemized list of permitted deductions.",
    evidence_quotes: ["The Landlord may deduct any amount from the deposit for any reason, at the Landlord's sole discretion.", "The remaining balance, if any, will be returned within 90 days after the Tenant vacates."],
    confidence: "high"
  },
  "what happens if i leave early?": {
    answer: "The agreement says you must give two months' written notice to end the tenancy early. It does not explain whether there are additional charges for leaving early, so consider asking for that to be clarified in writing.",
    evidence_quotes: ["The Tenant must give two months' written notice to end the tenancy early."],
    confidence: "medium"
  }
};
const MOCK_ANSWERS_HI = {
  "what is the notice period?": {
    answer: "समझौते के अनुसार किरायेदारी जल्दी समाप्त करने के लिए आपको दो महीने पहले लिखित सूचना देनी होगी। यह उत्तर दस्तावेज़ की समय से पहले समाप्ति वाली शर्त पर आधारित है।",
    evidence_quotes: ["किरायेदारी समय से पहले समाप्त करने के लिए किरायेदार को दो महीने का लिखित नोटिस देना होगा।"],
    confidence: "high"
  },
  "can the landlord keep my deposit?": {
    answer: "दस्तावेज़ कहता है कि मकान मालकिन अपने विवेक से किसी भी कारण से जमा राशि काट सकती हैं और शेष राशि 90 दिनों के भीतर लौटाएंगी। समझौते में कटौती के मान्य कारणों की सूची नहीं है।",
    evidence_quotes: ["मकान मालकिन अपने विवेक से किसी भी कारण से जमा राशि काट सकती हैं।"],
    confidence: "high"
  },
  "what happens if i leave early?": {
    answer: "समझौते के अनुसार किरायेदारी जल्दी समाप्त करने के लिए आपको दो महीने पहले लिखित सूचना देनी होगी। जल्दी जाने पर कोई अतिरिक्त शुल्क होगा या नहीं, यह स्पष्ट नहीं है।",
    evidence_quotes: ["किरायेदारी समय से पहले समाप्त करने के लिए किरायेदार को दो महीने का लिखित नोटिस देना होगा।"],
    confidence: "medium"
  }
};

const elements = {
  text: document.querySelector("#document-text"),
  file: document.querySelector("#document-file"),
  dropZone: document.querySelector("#drop-zone"),
  preview: document.querySelector("#file-preview"),
  previewImage: document.querySelector("#preview-image"),
  fileName: document.querySelector("#file-name"),
  fileSize: document.querySelector("#file-size"),
  removeFile: document.querySelector("#remove-file"),
  sample: document.querySelector("#sample-button"),
  analyze: document.querySelector("#analyze-button"),
  formError: document.querySelector("#form-error"),
  empty: document.querySelector("#empty-state"),
  loading: document.querySelector("#loading-state"),
  error: document.querySelector("#error-state"),
  errorTitle: document.querySelector("#error-title"),
  errorMessage: document.querySelector("#error-message"),
  retry: document.querySelector("#retry-button"),
  results: document.querySelector("#results-state"),
  charCount: document.querySelector("#char-count"),
  apiBase: document.querySelector("#api-base"),
  timer: document.querySelector("#elapsed-time"),
  toast: document.querySelector("#toast"),
  askForm: document.querySelector("#ask-form"),
  askInput: document.querySelector("#ask-input"),
  chat: document.querySelector("#chat-messages")
};

let selectedFile = null;
let currentAnalysis = null;
// Keep only the active result in browser memory; the demo does not persist documents.
let timerInterval = null;
let toastTimeout = null;
let lastAnalyzeRequest = null;
const isMockMode = new URLSearchParams(window.location.search).get("mock") === "1";

function defaultApiBase() {
  return window.location.protocol === "file:" ? "http://localhost:8000" : window.location.origin;
}

function getApiBase() {
  return elements.apiBase.value.trim().replace(/\/+$/, "") || defaultApiBase();
}

function setToast(message) {
  elements.toast.textContent = message;
  elements.toast.classList.add("show");
  window.clearTimeout(toastTimeout);
  toastTimeout = window.setTimeout(() => elements.toast.classList.remove("show"), 2800);
}

function selectedLanguage() {
  return document.querySelector('input[name="language"]:checked').value;
}

function updateCharCount() {
  const length = elements.text.value.length;
  elements.charCount.textContent = `${length.toLocaleString()} / 20,000`;
  elements.charCount.classList.toggle("char-limit", length >= MAX_TEXT_LENGTH);
}

function readableSize(bytes) {
  return bytes < 1024 * 1024 ? `${(bytes / 1024).toFixed(0)} KB` : `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function clearFile() {
  selectedFile = null;
  elements.file.value = "";
  elements.preview.hidden = true;
  const previewUrl = elements.previewImage.src;
  if (previewUrl.startsWith("blob:")) URL.revokeObjectURL(previewUrl);
  elements.previewImage.removeAttribute("src");
}

function acceptFile(file) {
  if (!file) return;
  const acceptedTypes = ["image/png", "image/jpeg", "image/webp"];
  const extensionMatches = /\.(png|jpe?g|webp)$/i.test(file.name);
  if (!acceptedTypes.includes(file.type) && !extensionMatches) {
    showInlineError("Please choose a PNG, JPG, or WEBP image.");
    return;
  }
  if (file.size > MAX_FILE_BYTES) {
    showInlineError("That image is larger than 5 MB. Please choose a smaller file.");
    return;
  }
  clearInlineError();
  clearFile();
  selectedFile = file;
  elements.fileName.textContent = file.name;
  elements.fileSize.textContent = readableSize(file.size);
  elements.previewImage.src = URL.createObjectURL(file);
  elements.preview.hidden = false;
}

function showInlineError(message) {
  elements.formError.textContent = message;
  elements.formError.hidden = false;
}

function clearInlineError() {
  elements.formError.textContent = "";
  elements.formError.hidden = true;
}

function setView(view) {
  elements.empty.hidden = view !== "empty";
  elements.loading.hidden = view !== "loading";
  elements.error.hidden = view !== "error";
  elements.results.hidden = view !== "results";
}

function startTimer() {
  const start = Date.now();
  elements.timer.textContent = "0";
  window.clearInterval(timerInterval);
  timerInterval = window.setInterval(() => {
    elements.timer.textContent = String(Math.floor((Date.now() - start) / 1000));
  }, 250);
}

function stopTimer() {
  window.clearInterval(timerInterval);
  timerInterval = null;
}

function formatApiError(status, body) {
  if (status === 413) return ["Image too large", "This image exceeds the 5 MB upload limit. Choose a smaller image and try again."];
  if (status === 422) return ["Please check your document", typeof body.detail === "string" ? body.detail : "Add document text or choose an image, then try again."];
  if (status === 502) return ["Gemma couldn't complete the analysis", typeof body.detail === "string" ? body.detail : "The model service returned an error. Please try again in a moment."];
  if (status === 404) return ["Analysis not found", "This document analysis is no longer available. Analyze the document again before asking a question."];
  return ["Something went wrong", typeof body.detail === "string" ? body.detail : `The request failed (HTTP ${status}). Please try again.`];
}

async function requestAnalysis(text, file, language) {
  if (isMockMode) {
    await new Promise((resolve) => window.setTimeout(resolve, 750));
    return language === "hi" ? MOCK_ANALYSIS_HI : MOCK_ANALYSIS_EN;
  }
  const formData = new FormData();
  if (text.trim()) formData.append("text", text.trim());
  if (file) formData.append("file", file);
  formData.append("language", language);

  const response = await fetch(`${getApiBase()}${API_PATH}/analyze`, { method: "POST", body: formData });
  let body = {};
  try { body = await response.json(); } catch { /* The status still determines the user-facing error. */ }
  if (!response.ok) {
    const [title, message] = formatApiError(response.status, body);
    const error = new Error(message);
    error.title = title;
    error.status = response.status;
    throw error;
  }
  return body;
}

function validateAnalysis(data) {
  const arrayFields = ["key_clauses", "risk_flags", "questions_to_ask"];
  if (!data || typeof data.analysis_id !== "string" || typeof data.document_type !== "string" ||
      typeof data.plain_summary !== "string" || arrayFields.some((field) => !Array.isArray(data[field])) ||
      typeof data.model !== "string" || typeof data.disclaimer !== "string") {
    throw new Error("The API response did not match the document analysis contract.");
  }
}

function textNode(tag, className, value) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  node.textContent = value;
  return node;
}

function renderAnalysis(data) {
  validateAnalysis(data);
  currentAnalysis = data;
  document.querySelector("#document-type").textContent = data.document_type;
  document.querySelector("#plain-summary").textContent = data.plain_summary;
  const modelBadge = document.querySelector("#model-badge");
  modelBadge.setAttribute("aria-label", `Powered by Gemma 4 (open weights), model ${data.model}`);
  modelBadge.querySelector("small").textContent = `(open weights) · ${data.model}`;
  document.querySelector("#clause-count").textContent = String(data.key_clauses.length);
  document.querySelector("#risk-count").textContent = String(data.risk_flags.length);

  const clauseList = document.querySelector("#clauses-list");
  clauseList.replaceChildren();
  data.key_clauses.forEach((clause, index) => {
    const details = document.createElement("details");
    details.className = "clause-card";
    if (index === 0) details.open = true;
    const summary = textNode("summary", "", clause.title);
    const content = document.createElement("div");
    content.className = "clause-content";
    content.append(textNode("blockquote", "quote", `“${clause.quote}”`), textNode("p", "clause-explanation", clause.explanation));
    details.append(summary, content);
    clauseList.append(details);
  });

  const riskList = document.querySelector("#risks-list");
  riskList.replaceChildren();
  data.risk_flags.forEach((risk) => {
    const card = document.createElement("article");
    card.className = "risk-card";
    card.dataset.level = risk.risk_level;
    const heading = document.createElement("div");
    heading.className = "risk-heading";
    heading.append(textNode("strong", "", risk.clause_title));
    const level = textNode("span", `risk-level ${risk.risk_level}`, risk.risk_level);
    heading.append(level);
    const quote = textNode("button", "risk-quote", `“${risk.quote}”`);
    quote.type = "button";
    quote.title = "Highlight this passage in the pasted document";
    quote.addEventListener("click", () => highlightQuote(risk.quote));
    card.append(heading, quote, textNode("p", "risk-reason", risk.reason));
    riskList.append(card);
  });

  const questions = document.querySelector("#questions-list");
  questions.replaceChildren(...data.questions_to_ask.map((question) => textNode("li", "", question)));
  document.querySelector("#disclaimer").textContent = data.disclaimer || DISCLAIMER;
  elements.chat.replaceChildren();
  setView("results");
}

function highlightQuote(quote) {
  const source = elements.text.value;
  const index = source.indexOf(quote);
  if (index < 0) {
    setToast("This quote isn't in the pasted text. It may come from the uploaded image.");
    return;
  }
  elements.text.focus();
  elements.text.setSelectionRange(index, index + quote.length);
  elements.text.scrollIntoView({ behavior: "smooth", block: "center" });
}

function showError(error) {
  stopTimer();
  elements.errorTitle.textContent = error.title || "We couldn't analyze this document.";
  if (error instanceof TypeError && !error.status) {
    elements.errorTitle.textContent = "Couldn't reach the API";
    elements.errorMessage.textContent = "Check that the backend is running and that the API base URL below is correct.";
  } else {
    elements.errorMessage.textContent = error.message || "Please try again.";
  }
  setView("error");
}

async function analyze() {
  const text = elements.text.value;
  const language = selectedLanguage();
  if (!text.trim() && !selectedFile) {
    showInlineError("Paste document text or add an image before analyzing.");
    elements.text.focus();
    return;
  }
  if (text.length > MAX_TEXT_LENGTH) {
    showInlineError("Document text must be 20,000 characters or fewer.");
    return;
  }
  clearInlineError();
  lastAnalyzeRequest = { text, file: selectedFile, language };
  elements.analyze.disabled = true;
  setView("loading");
  startTimer();
  try {
    const data = await requestAnalysis(text, selectedFile, language);
    renderAnalysis(data);
  } catch (error) {
    showError(error);
  } finally {
    stopTimer();
    elements.analyze.disabled = false;
  }
}

function appendChatMessage(role, content) {
  const message = textNode("div", `chat-message ${role}`, content);
  elements.chat.append(message);
  message.scrollIntoView({ behavior: "smooth", block: "nearest" });
  return message;
}

async function requestAnswer(question, language) {
  if (isMockMode) {
    await new Promise((resolve) => window.setTimeout(resolve, 450));
    const canned = MOCK_ANSWERS[question.trim().toLowerCase()];
    if (canned) {
      const localized = language === "hi" ? MOCK_ANSWERS_HI[question.trim().toLowerCase()] : canned;
      return { ...localized, disclaimer: language === "hi" ? MOCK_ANALYSIS_HI.disclaimer : DISCLAIMER };
    }
    return {
      answer: language === "hi"
        ? "मुझे इस प्रश्न का उत्तर देने के लिए दस्तावेज़ में पर्याप्त जानकारी नहीं मिली। कृपया किसी योग्य कानूनी पेशेवर से पूछें।"
        : "I couldn't find enough information in this document to answer that confidently. Consider asking a qualified legal professional.",
      evidence_quotes: [],
      confidence: "low",
      disclaimer: DISCLAIMER
    };
  }
  const response = await fetch(`${getApiBase()}${API_PATH}/ask`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ analysis_id: currentAnalysis.analysis_id, question, language })
  });
  let body = {};
  try { body = await response.json(); } catch { /* Report the HTTP status when the server omits JSON. */ }
  if (!response.ok) {
    const [title, message] = formatApiError(response.status, body);
    const error = new Error(message);
    error.title = title;
    error.status = response.status;
    throw error;
  }
  return body;
}

async function askQuestion(question) {
  if (!currentAnalysis || !question.trim()) return;
  const cleanQuestion = question.trim();
  const language = selectedLanguage();
  appendChatMessage("user", cleanQuestion);
  elements.askInput.value = "";
  elements.askInput.disabled = true;
  elements.askForm.querySelector("button").disabled = true;
  const pending = appendChatMessage("assistant", "Looking through your document...");
  try {
    const answer = await requestAnswer(cleanQuestion, language);
    pending.replaceChildren(document.createTextNode(answer.answer));
    answer.evidence_quotes.forEach((quote) => pending.append(textNode("blockquote", "quote", `“${quote}”`)));
    const confidence = textNode("span", `confidence-chip ${answer.confidence}`, `${answer.confidence} confidence`);
    confidence.dataset.level = answer.confidence;
    pending.append(confidence);
    pending.append(textNode("small", "chat-disclaimer", answer.disclaimer || DISCLAIMER));
  } catch (error) {
    pending.textContent = error instanceof TypeError && !error.status
      ? "Couldn't reach the API. Check the API base URL and try again."
      : error.message || "Couldn't answer that question. Please try again.";
    pending.classList.add("chat-error");
  } finally {
    elements.askInput.disabled = false;
    elements.askForm.querySelector("button").disabled = false;
    elements.askInput.focus();
  }
}

elements.text.addEventListener("input", updateCharCount);
elements.file.addEventListener("change", () => acceptFile(elements.file.files[0]));
elements.removeFile.addEventListener("click", clearFile);
elements.analyze.addEventListener("click", analyze);
elements.retry.addEventListener("click", () => {
  if (lastAnalyzeRequest) {
    elements.text.value = lastAnalyzeRequest.text;
    if (selectedFile !== lastAnalyzeRequest.file) selectedFile = lastAnalyzeRequest.file;
    analyze();
  }
});
elements.sample.addEventListener("click", () => {
  elements.text.value = selectedLanguage() === "hi" ? SAMPLE_HI : SAMPLE_EN;
  updateCharCount();
  clearInlineError();
  elements.text.focus();
  elements.text.setSelectionRange(0, 0);
  elements.text.scrollTop = 0;
  setToast("Sample rental agreement added.");
});
elements.dropZone.addEventListener("keydown", (event) => {
  if (event.key === "Enter" || event.key === " ") {
    event.preventDefault();
    elements.file.click();
  }
});
["dragenter", "dragover"].forEach((eventName) => elements.dropZone.addEventListener(eventName, (event) => {
  event.preventDefault();
  elements.dropZone.classList.add("is-dragging");
}));
["dragleave", "drop"].forEach((eventName) => elements.dropZone.addEventListener(eventName, (event) => {
  event.preventDefault();
  elements.dropZone.classList.remove("is-dragging");
}));
elements.dropZone.addEventListener("drop", (event) => acceptFile(event.dataTransfer.files[0]));
document.querySelectorAll(".question-chip").forEach((chip) => chip.addEventListener("click", () => askQuestion(chip.textContent)));
elements.askForm.addEventListener("submit", (event) => {
  event.preventDefault();
  askQuestion(elements.askInput.value);
});
document.querySelectorAll('input[name="language"]').forEach((radio) => radio.addEventListener("change", () => {
  if (!elements.text.value.trim()) return;
  if (elements.text.value === SAMPLE_EN || elements.text.value === SAMPLE_HI) {
    elements.text.value = selectedLanguage() === "hi" ? SAMPLE_HI : SAMPLE_EN;
    updateCharCount();
  }
}));

const savedApiBase = window.localStorage.getItem("jurify-api-base");
elements.apiBase.value = savedApiBase || defaultApiBase();
elements.apiBase.addEventListener("change", () => window.localStorage.setItem("jurify-api-base", elements.apiBase.value.trim()));
updateCharCount();
if (isMockMode) setToast("Demo mode is on - no API connection needed.");

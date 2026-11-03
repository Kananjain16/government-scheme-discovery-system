if (typeof API_BASE_URL === "undefined") {
    throw new Error(
        "API_BASE_URL is not defined. Load js/config.js before js/app.js."
    );
}

async function apiRequest(endpoint, payload) {
    let response;

    try {
        response = await fetch(`${API_BASE_URL}${endpoint}`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(payload)
        });
    } catch (error) {
        throw new Error(
            "Cannot connect to the Flask backend. Make sure Flask is running on http://127.0.0.1:5000."
        );
    }

    let data;

    try {
        data = await response.json();
    } catch {
        throw new Error(
            `The server returned an invalid response. HTTP ${response.status}.`
        );
    }

    if (!response.ok) {
        const message =
            data?.error ||
            data?.message ||
            data?.details ||
            `Request failed. HTTP ${response.status}.`;

        throw new Error(
            typeof message === "string" ? message : JSON.stringify(message)
        );
    }

    return data;
}


/* -----------------------------
   2. SEARCH INTERFACE
----------------------------- */

const searchInput = document.getElementById("searchQuery");
const searchButton = document.getElementById("searchButton");
const searchMethod = document.getElementById("searchMethod");
const resultLimit = document.getElementById("resultLimit");

const resultsContainer = document.getElementById("resultsContainer");
const statusMessage = document.getElementById("statusMessage");
const resultCount = document.getElementById("resultCount");

function showStatus(message, isError = false) {
    if (!statusMessage) return;

    statusMessage.textContent = message;
    statusMessage.classList.toggle("error", isError);
}

function setSearchLoading(isLoading) {
    if (!searchButton) return;

    searchButton.disabled = isLoading;
    searchButton.textContent = isLoading ? "Searching..." : "Search Schemes";
}

function showSearchError(message) {
    if (!resultsContainer) return;

    resultsContainer.replaceChildren();

    const wrapper = document.createElement("div");
    wrapper.className = "empty-state";

    const heading = document.createElement("h3");
    heading.textContent = "Unable to load schemes";

    const paragraph = document.createElement("p");
    paragraph.textContent = message;

    wrapper.append(heading, paragraph);
    resultsContainer.appendChild(wrapper);

    if (resultCount) resultCount.textContent = "";
}


/* -----------------------------
   3. USER PROFILE FORM
----------------------------- */

const profileForm = document.getElementById("profileForm");
const profileStatus = document.getElementById("profileStatus");

let userProfile = null;

function showProfileStatus(message, type) {
    if (!profileStatus) return;

    profileStatus.textContent = message;
    profileStatus.classList.remove("success", "error");

    if (type) {
        profileStatus.classList.add(type);
    }
}

function collectProfile() {
    const ageElement = document.getElementById("age");
    const incomeElement = document.getElementById("annual_income");
    const stateElement = document.getElementById("state");
    const occupationElement = document.getElementById("occupation");
    const genderElement = document.getElementById("gender");
    const categoryElement = document.getElementById("category");

    const ageValue = ageElement?.value.trim() ?? "";
    const incomeValue = incomeElement?.value.trim() ?? "";

    return {
        age: ageValue === "" ? null : Number(ageValue),
        annual_income: incomeValue === "" ? null : Number(incomeValue),
        state: stateElement?.value.trim() ?? "",
        occupation: occupationElement?.value.trim() ?? "",
        gender: genderElement?.value ?? "",
        category: categoryElement?.value ?? ""
    };
}

function validateProfile(profile) {
    if (
        profile.age !== null &&
        (
            !Number.isFinite(profile.age) ||
            !Number.isInteger(profile.age) ||
            profile.age < 0 ||
            profile.age > 120
        )
    ) {
        return "Age must be a whole number between 0 and 120.";
    }

    if (
        profile.annual_income !== null &&
        (
            !Number.isFinite(profile.annual_income) ||
            profile.annual_income < 0
        )
    ) {
        return "Annual income must be a valid non-negative number.";
    }

    return null;
}

if (profileForm) {
    profileForm.addEventListener("submit", (event) => {
        event.preventDefault();

        const profile = collectProfile();
        const error = validateProfile(profile);

        if (error) {
            userProfile = null;
            showProfileStatus(error, "error");
            return;
        }

        userProfile = profile;

        showProfileStatus(
            "Profile collected successfully. It will be sent with your next scheme discovery request.",
            "success"
        );
    });

    profileForm.addEventListener("reset", () => {
        userProfile = null;
        showProfileStatus("Profile cleared.", "success");
    });
}


/* -----------------------------
   4. DISCOVERY RESULT ELEMENTS
----------------------------- */

const eligibleResults = document.getElementById("eligibleResults");
const verificationResults = document.getElementById("verificationResults");
const notEligibleResults = document.getElementById("notEligibleResults");

const eligibleCount = document.getElementById("eligibleCount");
const verificationCount = document.getElementById("verificationCount");
const notEligibleCount = document.getElementById("notEligibleCount");

const resultsSummary = document.getElementById("resultsSummary");

const schemeDetailsDialog = document.getElementById("schemeDetailsDialog");
const detailSchemeName = document.getElementById("detailSchemeName");
const schemeDetailsContent = document.getElementById("schemeDetailsContent");
const closeDetailsButton = document.getElementById("closeDetailsButton");

let currentSchemes = [];

function createTextElement(tag, className, text) {
    const element = document.createElement(tag);

    if (className) {
        element.className = className;
    }

    element.textContent =
        text === undefined || text === null || text === ""
            ? "Not available."
            : String(text);

    return element;
}

function getUnknownConditionText(condition) {
    if (typeof condition === "string") {
        return condition;
    }

    if (condition && typeof condition === "object") {
        return [
            condition.field_name,
            condition.reason,
            condition.value
        ].filter(Boolean).join(": ");
    }

    return "Additional information is required.";
}

function getSchemeDescription(scheme) {
    // The actual /api/discover response does not currently return
    // a "description" property. Use eligibility_description as
    // the explanatory text instead.
    return (
        scheme.description ||
        scheme.eligibility_description ||
        "Description not available."
    );
}

function renderSchemeCard(scheme) {
    const card = document.createElement("article");
    card.className = "scheme-card";

    const heading = createTextElement(
        "h4",
        "",
        scheme.scheme_name || `Scheme ${scheme.scheme_id ?? ""}`
    );

    const description = createTextElement(
        "p",
        "scheme-description",
        getSchemeDescription(scheme)
    );

    const status = scheme.eligibility?.status || "needs_verification";

    const allowedStatuses = [
        "potentially_eligible",
        "needs_verification",
        "not_eligible"
    ];

    const safeStatus = allowedStatuses.includes(status)
        ? status
        : "needs_verification";

    const statusLabel = createTextElement(
        "span",
        `status-label status-${safeStatus}`,
        safeStatus.replaceAll("_", " ").toUpperCase()
    );

    const meta = document.createElement("div");
    meta.className = "scheme-meta";

    meta.appendChild(
        createTextElement(
            "span",
            "",
            `Scheme ID: ${scheme.scheme_id ?? "N/A"}`
        )
    );

    meta.appendChild(
        createTextElement(
            "span",
            "",
            `Level: ${scheme.level || "N/A"}`
        )
    );

    const retrievalScore =
        scheme.retrieval_score ?? scheme.score;

    if (
        retrievalScore !== undefined &&
        retrievalScore !== null &&
        Number.isFinite(Number(retrievalScore))
    ) {
        meta.appendChild(
            createTextElement(
                "span",
                "",
                `Retrieval score: ${Number(retrievalScore).toFixed(4)}`
            )
        );
    }

    if (scheme.rank !== undefined && scheme.rank !== null) {
        meta.appendChild(
            createTextElement("span", "", `Rank: ${scheme.rank}`)
        );
    }

    const benefits = createTextElement(
        "p",
        "scheme-benefits",
        scheme.benefits || "Benefits information not available."
    );

    const reason = createTextElement(
        "p",
        "eligibility-reason",
        scheme.eligibility?.reason ||
            "No eligibility explanation available."
    );

    const unknownConditions =
        scheme.eligibility?.unknown_conditions || [];

    card.append(
        heading,
        description,
        statusLabel,
        meta,
        benefits,
        reason
    );

    if (Array.isArray(unknownConditions) && unknownConditions.length > 0) {
        const list = document.createElement("ul");
        list.className = "condition-list";

        unknownConditions.forEach((condition) => {
            const item = document.createElement("li");
            item.textContent = getUnknownConditionText(condition);
            list.appendChild(item);
        });

        card.appendChild(list);
    }

    const detailsButton = document.createElement("button");
    detailsButton.type = "button";
    detailsButton.textContent = "View Details";
    detailsButton.addEventListener("click", () => {
        showSchemeDetails(scheme);
    });

    card.appendChild(detailsButton);

    return card;
}

function renderGroup(container, schemes) {
    if (!container) return;

    container.replaceChildren();

    if (!Array.isArray(schemes) || schemes.length === 0) {
        const empty = createTextElement(
            "div",
            "no-results",
            "No schemes in this category."
        );

        container.appendChild(empty);
        return;
    }

    schemes.forEach((scheme) => {
        container.appendChild(renderSchemeCard(scheme));
    });
}

function addDetailSection(title, value) {
    const wrapper = document.createElement("div");
    wrapper.className = "detail-section";

    const heading = createTextElement("h3", "", title);
    const paragraph = createTextElement("p", "", value);

    wrapper.append(heading, paragraph);
    schemeDetailsContent.appendChild(wrapper);
}

function showSchemeDetails(scheme) {
    if (!schemeDetailsDialog || !schemeDetailsContent || !detailSchemeName) {
        return;
    }

    detailSchemeName.textContent =
        scheme.scheme_name || `Scheme ${scheme.scheme_id ?? ""}`;

    schemeDetailsContent.replaceChildren();

    addDetailSection("Scheme ID", scheme.scheme_id);
    addDetailSection("Scheme level", scheme.level);
    addDetailSection("Rank", scheme.rank);
    addDetailSection(
        "Retrieval score",
        scheme.retrieval_score ?? scheme.score
    );
    addDetailSection("Benefits", scheme.benefits);
    addDetailSection(
        "Eligibility description",
        scheme.eligibility_description
    );
    addDetailSection(
        "Eligibility status",
        scheme.eligibility?.status
    );
    addDetailSection(
        "Eligibility reason",
        scheme.eligibility?.reason
    );

    const unknownConditions =
        scheme.eligibility?.unknown_conditions || [];

    const unknownText = Array.isArray(unknownConditions)
        ? unknownConditions.map(getUnknownConditionText).join("\n")
        : "Not available.";

    addDetailSection(
        "Conditions needing verification",
        unknownText
    );

    if (typeof schemeDetailsDialog.showModal === "function") {
        schemeDetailsDialog.showModal();
    } else {
        schemeDetailsDialog.setAttribute("open", "");
    }
}


/* -----------------------------
   5. RENDER ACTUAL API RESPONSE
----------------------------- */

function renderDiscoveryResults(apiResponse) {
    /*
      Actual response shape confirmed in Postman:

      {
        "success": true,
        "data": {
          "results": {
            "potentially_eligible": [],
            "needs_verification": [],
            "not_eligible": []
          },
          "summary": {},
          "total_retrieved": 10,
          "retrieval_method": "semantic"
        },
        "message": "..."
      }
    */

    if (!apiResponse || apiResponse.success !== true) {
        throw new Error(
            apiResponse?.message || "Discovery API did not return success."
        );
    }

    const groups = apiResponse.data?.results;

    if (!groups || typeof groups !== "object") {
        throw new Error(
            "Unexpected discovery response: data.results was not found. Check the browser console."
        );
    }

    const eligible = groups.potentially_eligible;
    const verification = groups.needs_verification;
    const notEligible = groups.not_eligible;

    if (
        !Array.isArray(eligible) ||
        !Array.isArray(verification) ||
        !Array.isArray(notEligible)
    ) {
        throw new Error(
            "Unexpected discovery response: one or more eligibility groups are not arrays."
        );
    }

    currentSchemes = [
        ...eligible,
        ...verification,
        ...notEligible
    ];

    if (eligibleCount) eligibleCount.textContent = eligible.length;
    if (verificationCount) verificationCount.textContent = verification.length;
    if (notEligibleCount) notEligibleCount.textContent = notEligible.length;

    if (resultsSummary) {
        const total = apiResponse.data.total_retrieved ?? currentSchemes.length;
        const method = apiResponse.data.retrieval_method || "unknown";

        resultsSummary.textContent =
            `Found ${total} schemes using ${method.toUpperCase()} search. ` +
            `Potentially eligible: ${eligible.length}, ` +
            `Needs verification: ${verification.length}, ` +
            `Not eligible: ${notEligible.length}.`;
    }

    renderGroup(eligibleResults, eligible);
    renderGroup(verificationResults, verification);
    renderGroup(notEligibleResults, notEligible);

    const discoverySection = document.getElementById("discoveryResults");

    if (discoverySection) {
        discoverySection.scrollIntoView({ behavior: "smooth" });
    }
}


/* -----------------------------
   6. CALL POST /api/discover
----------------------------- */

async function handleSearch() {
    if (!searchInput || !searchMethod || !resultLimit) {
        showStatus("Search form elements are missing from index.html.", true);
        return;
    }

    const query = searchInput.value.trim();

    if (!query) {
        showStatus("Please enter a search query.", true);
        searchInput.focus();
        return;
    }

    const method = searchMethod.value;
    const topK = Number(resultLimit.value);

    if (!Number.isInteger(topK) || topK < 1) {
        showStatus("Please select a valid result limit.", true);
        return;
    }

    /*
      If the profile form has been submitted, send its values.
      Otherwise send an empty object, as in the Day 22 instructions.
    */
    const profile = userProfile || {};

    const payload = {
        query: query,
        method: method,
        top_k: topK,
        profile: profile
    };

    setSearchLoading(true);
    showStatus("Searching government schemes...");

    if (resultsContainer) resultsContainer.replaceChildren();
    if (resultCount) resultCount.textContent = "";
    if (resultsSummary) resultsSummary.textContent = "";

    try {
        const data = await apiRequest("/api/discover", payload);

        console.log("Actual discovery API response:", data);

        renderDiscoveryResults(data);

        if (resultCount) {
            resultCount.textContent =
                `${currentSchemes.length} results`;
        }

        showStatus(
            data.message || "Discovery request completed successfully."
        );
    } catch (error) {
        console.error("Discovery API error:", error);

        showStatus(
            error.message || "Unable to retrieve schemes.",
            true
        );

        showSearchError(
            error.message || "Please check your backend and try again."
        );
    } finally {
        setSearchLoading(false);
    }
}

if (searchButton) {
    searchButton.addEventListener("click", handleSearch);
}

if (searchInput) {
    searchInput.addEventListener("keydown", (event) => {
        if (event.key === "Enter") {
            event.preventDefault();
            handleSearch();
        }
    });
}


/* -----------------------------
   7. DETAILS DIALOG EVENTS
----------------------------- */

if (closeDetailsButton && schemeDetailsDialog) {
    closeDetailsButton.addEventListener("click", () => {
        schemeDetailsDialog.close();
    });
}

if (schemeDetailsDialog) {
    schemeDetailsDialog.addEventListener("click", (event) => {
        if (event.target === schemeDetailsDialog) {
            schemeDetailsDialog.close();
        }
    });
}


/* -----------------------------
   8. INITIAL STATE
----------------------------- */

// No sample schemes are rendered on page load.
// Results appear only after a successful real API request.
console.log("Government Scheme Discovery frontend initialized.");


/* =========================================================
   PART 8: RAG QUESTION ANSWERING
   Connects POST /api/rag/ask.
   Expected response shape:
   {
       "answer": "...",
       "sources": [
           {
               "chunk_id": 1,
               "scheme_id": 6,
               "scheme_name": "...",
               "section_name": "...",
               "similarity_score": 0.8
           }
       ]
   }
   Confirm this shape against your actual Postman response.
========================================================= */

const ragQuestion = document.getElementById("ragQuestion");
const ragSchemeId = document.getElementById("ragSchemeId");
const ragTopK = document.getElementById("ragTopK");
const askRagButton = document.getElementById("askRagButton");
const ragStatus = document.getElementById("ragStatus");
const ragAnswer = document.getElementById("ragAnswer");
const ragSources = document.getElementById("ragSources");

function showRagStatus(message, isError = false) {
    if (!ragStatus) return;

    ragStatus.textContent = message;
    ragStatus.classList.toggle("error", isError);
}

function displayRagAnswer(answer) {
    if (!ragAnswer) return;

    ragAnswer.replaceChildren();

    const heading = document.createElement("h3");
    heading.textContent = "AI Generated Answer";

    const answerText = document.createElement("p");
    answerText.textContent = answer;

    ragAnswer.append(heading, answerText);
}

function displayRagSources(sources) {
    if (!ragSources) return;

    ragSources.replaceChildren();

    if (!Array.isArray(sources) || sources.length === 0) {
        const note = document.createElement("p");
        note.textContent = "No source metadata was returned by the API.";
        ragSources.appendChild(note);
        return;
    }

    const heading = document.createElement("h3");
    heading.textContent = "Sources Used";
    ragSources.appendChild(heading);

    sources.forEach((source, index) => {
        const card = document.createElement("article");
        card.className = "rag-source-card";

        const sourceHeading = document.createElement("h4");
        sourceHeading.textContent = `Source ${index + 1}`;
        card.appendChild(sourceHeading);

        const fields = [
            ["Scheme", source.scheme_name],
            ["Scheme ID", source.scheme_id],
            ["Section", source.section_name],
            ["Chunk ID", source.chunk_id],
            ["Similarity score", source.similarity_score]
        ];

        fields.forEach(([label, value]) => {
            const paragraph = document.createElement("p");
            paragraph.textContent =
                `${label}: ${value === undefined || value === null || value === "" ? "Not provided" : value}`;
            card.appendChild(paragraph);
        });

        ragSources.appendChild(card);
    });
}

async function handleRagQuestion() {
    if (!ragQuestion || !ragTopK || !askRagButton) {
        showRagStatus("RAG form elements are missing from index.html.", true);
        return;
    }

    const question = ragQuestion.value.trim();
    const schemeIdValue = ragSchemeId?.value.trim() ?? "";

    if (!question) {
        showRagStatus("Please enter a question.", true);
        ragQuestion.focus();
        return;
    }

    const topK = Number(ragTopK.value);

    if (!Number.isInteger(topK) || topK < 1) {
        showRagStatus("Please select a valid context chunk count.", true);
        return;
    }

    const payload = {
        question: question,
        top_k: topK
    };

    if (schemeIdValue !== "") {
        const schemeId = Number(schemeIdValue);

        if (!Number.isInteger(schemeId) || schemeId <= 0) {
            showRagStatus("Enter a valid positive scheme ID.", true);
            ragSchemeId?.focus();
            return;
        }

        payload.scheme_id = schemeId;
    }

    askRagButton.disabled = true;
    askRagButton.textContent = "Generating answer...";
    showRagStatus("Retrieving scheme information and generating an answer...");

    if (ragAnswer) ragAnswer.replaceChildren();
    if (ragSources) ragSources.replaceChildren();

    try {
        const data = await apiRequest("/api/rag/ask", payload);

        console.log("Actual RAG API response:", data);

        // The current code expects data.answer and data.sources.
        // Change these paths if your actual Postman response is nested.
        if (typeof data.answer !== "string" || !data.answer.trim()) {
            throw new Error(
                "The RAG response does not contain a non-empty data.answer field. Inspect the console response and adjust the response mapping."
            );
        }

        displayRagAnswer(data.answer);

        const sources = Array.isArray(data.sources) ? data.sources : [];
        displayRagSources(sources);

        showRagStatus("Answer generated successfully.");
    } catch (error) {
        console.error("RAG API error:", error);
        showRagStatus(
            error.message || "Unable to generate an answer.",
            true
        );
    } finally {
        askRagButton.disabled = false;
        askRagButton.textContent = "Ask Question";
    }
}

if (askRagButton) {
    askRagButton.addEventListener("click", handleRagQuestion);
}

if (ragQuestion) {
    ragQuestion.addEventListener("keydown", (event) => {
        if (event.key === "Enter" && (event.ctrlKey || event.metaKey)) {
            event.preventDefault();
            handleRagQuestion();
        }
    });
}

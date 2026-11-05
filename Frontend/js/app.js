
/* =====================================
   COMMON API FUNCTION
===================================== */

async function apiRequest(endpoint, body) {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify(body)
    });

    let data;

    try {
        data = await response.json();
    } catch {
        throw new Error("Backend returned an invalid response.");
    }

    if (!response.ok || data.success === false) {
        throw new Error(
            data.message || data.error || "Something went wrong."
        );
    }

    return data;
}


/* =====================================
   COMMON UI FUNCTIONS
===================================== */

function setStatus(id, message, type = "") {
    const element = document.getElementById(id);

    if (!element) {
        console.error(`Element not found: ${id}`);
        return;
    }

    element.textContent = message;
    element.className = `status ${type}`;
}


function escapeHTML(value) {
    return String(value ?? "").replace(/[&<>"']/g, char => ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#39;"
    })[char]);
}


/* =====================================
   PROFILE MANAGEMENT
===================================== */

// Collect all eight frontend profile fields.

function getProfile() {
    return {
        age: Number(document.getElementById("age").value),

        gender: document.getElementById("gender").value,

        state: document.getElementById("state").value.trim(),

        occupation: document.getElementById("occupation").value,

        annual_income: Number(
            document.getElementById("income").value
        ),

        education: document.getElementById("education").value,

        category: document.getElementById("category").value,

        disability: document.getElementById("disability").value
    };
}


// IMPORTANT:
// The current backend supports only six profile fields.
// Education and disability remain saved locally but
// are not sent to the eligibility engine.

function getSupportedProfile(profile) {
    return {
        age: profile.age,
        gender: profile.gender,
        state: profile.state,
        occupation: profile.occupation,
        annual_income: profile.annual_income,
        category: profile.category
    };
}


// Load saved profile from localStorage.

function loadProfile() {
    const saved = localStorage.getItem("schemeSathiProfile");

    if (!saved) return;

    try {
        const profile = JSON.parse(saved);

        const fields = {
            age: profile.age,
            gender: profile.gender,
            state: profile.state,
            occupation: profile.occupation,
            income: profile.annual_income,
            education: profile.education,
            category: profile.category,
            disability: profile.disability
        };

        Object.entries(fields).forEach(([id, value]) => {
            const element = document.getElementById(id);

            if (
                element &&
                value !== undefined &&
                value !== null
            ) {
                element.value = value;
            }
        });

    } catch (error) {
        console.error("Could not load saved profile:", error);
    }
}


/* =====================================
   SAVE PROFILE AND FIND SCHEMES
===================================== */

document.getElementById("profileForm").addEventListener(
    "submit",
    async function(event) {

        event.preventDefault();

        const profile = getProfile();

        // Validate age.

        if (
            !Number.isFinite(profile.age) ||
            profile.age < 1 ||
            profile.age > 120
        ) {
            setStatus(
                "profileStatus",
                "Please enter a valid age.",
                "error"
            );

            return;
        }

        // Validate annual income.

        if (
            !Number.isFinite(profile.annual_income) ||
            profile.annual_income < 0
        ) {
            setStatus(
                "profileStatus",
                "Please enter a valid annual family income.",
                "error"
            );

            return;
        }

        // Save complete profile locally.

        localStorage.setItem(
            "schemeSathiProfile",
            JSON.stringify(profile)
        );

        setStatus(
            "profileStatus",
            "Profile saved. Finding relevant schemes...",
            "success"
        );

        // Automatically find schemes.

        await getRecommendations(profile);
    }
);


/* =====================================
   SEMANTIC SCHEME DISCOVERY
===================================== */

async function discoverSchemes() {

    const query = document.getElementById("searchQuery")
        .value.trim();

    const topK = Number(
        document.getElementById("topK").value
    );

    const button = document.getElementById("searchBtn");

    const resultsContainer =
        document.getElementById("searchResults");


    // Validate query.

    if (!query) {

        setStatus(
            "searchStatus",
            "Please enter your search query.",
            "error"
        );

        return;
    }

    if (!Number.isInteger(topK) || topK < 1 || topK > 50) {

        setStatus(
            "searchStatus",
            "Please select a valid number of results.",
            "error"
        );

        return;
    }


    button.disabled = true;

    resultsContainer.innerHTML = "";

    setStatus(
        "searchStatus",
        "Searching for relevant schemes..."
    );


    try {

        // Load complete saved profile.

        const savedProfile = localStorage.getItem(
            "schemeSathiProfile"
        );

        const fullProfile = savedProfile
            ? JSON.parse(savedProfile)
            : {};


        // Send only supported fields to backend.

        const profile = getSupportedProfile(fullProfile);


        const response = await apiRequest(
            "/api/discover",
            {
                query: query,

                method: "semantic",

                top_k: topK,

                profile: profile
            }
        );


        const results = response.data?.results || {};


        renderGroupedResults(
            results,
            "searchResults"
        );


        setStatus(
            "searchStatus",
            "Scheme discovery completed.",
            "success"
        );


    } catch (error) {

        console.error("Semantic search error:", error);

        setStatus(
            "searchStatus",
            error.message,
            "error"
        );

    } finally {

        button.disabled = false;

    }
}


/* =====================================
   PROFILE-BASED RECOMMENDATIONS
===================================== */

async function getRecommendations(profile) {

    const container = document.getElementById(
        "recommendationResults"
    );

    const button = document.getElementById(
        "saveProfileBtn"
    );


    button.disabled = true;

    container.innerHTML = "";


    try {

        // Filter unsupported profile fields.

        const supportedProfile = getSupportedProfile(profile);


        // Call semantic discovery API.

        const response = await apiRequest(
            "/api/discover",
            {
                query:
                    "Find government schemes relevant to my personal profile, occupation and eligibility.",

                method: "semantic",

                top_k: 10,

                profile: supportedProfile
            }
        );


        // Extract grouped results.

        const results = response.data?.results || {};


        // Display recommendations.

        renderGroupedResults(
            results,
            "recommendationResults"
        );


        setStatus(
            "profileStatus",
            "Profile saved and recommendations generated.",
            "success"
        );


        // Scroll to recommendations.

        document.getElementById(
            "recommendations"
        ).scrollIntoView({
            behavior: "smooth"
        });


    } catch (error) {

        console.error(
            "Recommendation error:",
            error
        );

        setStatus(
            "profileStatus",
            "Profile saved locally, but recommendations failed: " +
                error.message,
            "error"
        );

    } finally {

        button.disabled = false;

    }
}


/* =====================================
   DISPLAY GROUPED SCHEME RESULTS
===================================== */

function renderGroupedResults(groups, containerId) {

    const container = document.getElementById(containerId);


    const groupConfig = [

        {
            key: "potentially_eligible",

            title: "Potentially Eligible",

            status: "Potentially eligible",

            className: "eligible"
        },

        {
            key: "needs_verification",

            title: "Needs Verification",

            status: "Eligibility needs verification",

            className: "verification"
        },

        {
            key: "not_eligible",

            title: "Not Eligible",

            status: "Not eligible",

            className: "not-eligible"
        }

    ];


    let html = "";

    let total = 0;


    groupConfig.forEach(group => {

        const schemes = Array.isArray(groups[group.key])
            ? groups[group.key]
            : [];


        if (!schemes.length) return;


        total += schemes.length;


        html += `
            <h3>${group.title}</h3>
        `;


        schemes.forEach(scheme => {

            html += createSchemeCard(
                scheme,
                group
            );

        });

    });


    if (total === 0) {

        container.innerHTML = `
            <div class="empty-state">
                No schemes found.

                Try another search query or update
                your profile details.
            </div>
        `;

        return;
    }


    container.innerHTML = html;

}


/* =====================================
   CREATE SCHEME CARD
===================================== */

function createSchemeCard(scheme, group) {

    const name =
        scheme.scheme_name ||
        scheme.name ||
        "Unnamed Scheme";

    const level =
        scheme.level ||
        "Government Scheme";

    const benefits =
        scheme.benefits ||
        "Information not available.";

    const eligibility =
        scheme.eligibility_description ||
        scheme.eligibility ||
        "Eligibility information not available.";

    const schemeId = scheme.scheme_id;

    return `
        <article class="scheme-card">

            <span class="scheme-level">
                ${escapeHTML(level)}
            </span>

            <h3>${escapeHTML(name)}</h3>

            <p>
                <strong>Benefits:</strong>
                ${escapeHTML(benefits)}
            </p>

            <p>
                <strong>Eligibility:</strong>
                ${escapeHTML(eligibility)}
            </p>

            <span class="eligibility-status ${group.className}">
                ${group.status}
            </span>

            <p>
                <button
                    class="primary-btn"
                    data-scheme-id="${escapeHTML(schemeId)}"
                    data-scheme-name="${escapeHTML(name)}"
                    onclick="askAboutScheme(
                        this.dataset.schemeId,
                        this.dataset.schemeName
                    )">

                    Ask AI About This Scheme

                </button>
            </p>

        </article>
    `;
}


/* =====================================
   RAG QUESTION ANSWERING
===================================== */

// Select a scheme before asking AI questions.


function askAboutScheme(schemeId, schemeName) {

    // Store ID internally for the RAG backend.
    document.getElementById("ragSchemeId").value =
        schemeId ?? "";

    // Display scheme name to the user.
    document.getElementById("ragSchemeName").value =
        schemeName || "";

    // Scroll to AI section.
    document.getElementById("ask-ai").scrollIntoView({
        behavior: "smooth"
    });

    document.getElementById("ragQuestion").focus();
}



/* =====================================
   ASK AI ABOUT GOVERNMENT SCHEMES
===================================== */

async function askAI() {

    const question = document.getElementById(
        "ragQuestion"
    ).value.trim();


    const schemeIdValue = document.getElementById(
        "ragSchemeId"
    ).value.trim();


    const button = document.getElementById(
        "askBtn"
    );


    const answerContainer = document.getElementById(
        "ragAnswer"
    );


    // Validate question.

    if (!question) {

        setStatus(
            "ragStatus",
            "Please enter your question.",
            "error"
        );

        return;
    }


    // Prepare RAG request.

    const payload = {

        question: question,

        top_k: 5

    };


    // Add scheme ID if selected.

    if (schemeIdValue) {

        const schemeId = Number(schemeIdValue);


        if (
            !Number.isInteger(schemeId) ||
            schemeId <= 0
        ) {

            setStatus(
                "ragStatus",
                "Please enter a valid scheme ID.",
                "error"
            );

            return;
        }


        payload.scheme_id = schemeId;

    }


    button.disabled = true;

    answerContainer.style.display = "none";

    answerContainer.innerHTML = "";


    setStatus(
        "ragStatus",
        "Retrieving scheme information and generating answer..."
    );


    try {

        // Call RAG API.

        const response = await apiRequest(
            "/api/rag/ask",
            payload
        );


        // Display generated answer and sources.

        displayRAGAnswer(response);


        setStatus(
            "ragStatus",
            "Answer generated successfully.",
            "success"
        );


    } catch (error) {

        console.error("RAG error:", error);


        setStatus(
            "ragStatus",
            error.message,
            "error"
        );

    } finally {

        button.disabled = false;

    }

}


/* =====================================
   DISPLAY RAG ANSWER AND SOURCES
===================================== */

function displayRAGAnswer(response) {

    const container = document.getElementById(
        "ragAnswer"
    );


    const answer =
        response.answer ||
        "No answer was returned.";


    const sources = Array.isArray(response.sources)
        ? response.sources
        : [];


    let html = `

        <h3>AI Generated Answer</h3>

        <p>
            ${escapeHTML(answer).replace(/\n/g, "<br>")}
        </p>

    `;


    // Display retrieved sources.

    if (sources.length > 0) {

        html += `

            <div class="rag-sources">

                <h3>Retrieved Sources</h3>

                <ul>

        `;


        sources.forEach(source => {

            html += `

                <li>

                    <strong>
                        ${escapeHTML(
                            source.scheme_name || "Scheme"
                        )}
                    </strong>

                    <br>

                    Scheme ID:

                    ${escapeHTML(
                        source.scheme_id ?? "N/A"
                    )}

                    <br>

                    Section:

                    ${escapeHTML(
                        source.section_name || "N/A"
                    )}

                </li>

            `;

        });


        html += `

                </ul>

            </div>

        `;

    }


    container.innerHTML = html;

    container.style.display = "block";

}


/* =====================================
   INITIALIZATION
===================================== */

document.addEventListener(
    "DOMContentLoaded",
    function() {

        loadProfile();

        console.log(
            "Government Scheme Discovery System initialized."
        );

    }
);

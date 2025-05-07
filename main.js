const scrollRevealOption = {
  distance: "50px",
  origin: "bottom",
  duration: 1000,
};

// header container
ScrollReveal().reveal(".header__container h1", scrollRevealOption);

ScrollReveal().reveal(".header__container h4", {
  ...scrollRevealOption,
  delay: 500,
});

ScrollReveal().reveal(".header__container .btn", {
  ...scrollRevealOption,
  delay: 1000,
});

// about container
ScrollReveal().reveal(".about__container .section__header", scrollRevealOption);
ScrollReveal().reveal(".about__container .section__subheader", {
  ...scrollRevealOption,
  delay: 500,
});

ScrollReveal().reveal(".about__container .about__flex", {
  ...scrollRevealOption,
  delay: 1000,
});

ScrollReveal().reveal(".about__container .btn", {
  ...scrollRevealOption,
  delay: 1500,
});

// discover container
ScrollReveal().reveal(".discover__card", {
  ...scrollRevealOption,
  interval: 500,
});

ScrollReveal().reveal(".discover__card__content", {
  ...scrollRevealOption,
  interval: 500,
  delay: 200,
});

// blogs container
ScrollReveal().reveal(".blogs__card", {
  duration: 1000,
  interval: 400,
});

// journals container
ScrollReveal().reveal(".journals__card", {
  ...scrollRevealOption,
  interval: 400,
});

const startTime = new Date("2024-05-05T18:00:00");

function updateLiveTime() {
  const now = new Date();
  let diff = Math.floor((now - startTime) / 1000); // total seconds

  const years = Math.floor(diff / (365.25 * 24 * 60 * 60));
  diff -= Math.floor(years * 365.25 * 24 * 60 * 60);

  const days = Math.floor(diff / (24 * 60 * 60));
  diff -= days * 24 * 60 * 60;

  const hours = Math.floor(diff / (60 * 60));
  diff -= hours * 60 * 60;

  const minutes = Math.floor(diff / 60);
  const seconds = diff % 60;

  // Format with leading zero
  const format = (n) => n.toString().padStart(2, '0');

  const timeString = `${years} Years : ${format(days)} Days : ${format(hours)} Hours : ${format(minutes)} Minutes : ${format(seconds)} Seconds`;

  document.getElementById("live-time").textContent = timeString;
}

updateLiveTime();
setInterval(updateLiveTime, 1000);

const journalUploadForm = document.getElementById("journalUploadForm");
const journalsGrid = document.getElementById("journalsGrid");

const toggleBtn = document.getElementById("toggleFormBtn");
const journalForm = document.getElementById("journalForm");

toggleBtn.addEventListener("click", () => {
  const isVisible = journalForm.style.display === "block";
  journalForm.style.display = isVisible ? "none" : "block";
  toggleBtn.innerHTML = isVisible
    ? 'Add New Journal <i class="ri-add-line"></i>'
    : 'Cancel <i class="ri-close-line"></i>';
});


journalUploadForm.addEventListener("submit", (e) => {
  e.preventDefault();

  const title = document.getElementById("journalTitle").value.trim();
  const date = document.getElementById("journalDate").value;
  const desc = document.getElementById("journalDescription").value.trim();
  const imageInput = document.getElementById("journalImageURL").value.trim();

  if (!title || !date || !desc || !imageInput) {
    alert("Please fill all fields including the image URL.");
    return;
  }

    // Extract Google Drive ID if full URL is given
  let imageURL = imageInput;
  if (imageInput.includes("drive.google.com")) {
    const match = imageInput.match(/[-\w]{25,}/); // Match long Drive file ID
    if (match) {
      imageURL = `https://drive.google.com/uc?export=view&id=${match[0]}`;
    } else {
      alert("Invalid Google Drive URL");
      return;
    }
  } else if (!imageInput.startsWith("https://")) {
  // Treat input as ID
    imageURL = `https://drive.google.com/uc?export=view&id=${imageInput}`;
  }

  const journalCard = document.createElement("div");
  journalCard.classList.add("journals__card");
  journalCard.innerHTML = `
    <img src="${imageURL}" alt="journal" />
    <div class="journals__content">
      <div class="journals__author">
        <img src="assets/author-placeholder.jpg" alt="author" />
        <p>By Us</p>
      </div>
      <h4 contenteditable="true">${title}</h4>
      <p contenteditable="true">${desc}</p>
      <div class="journals__footer">
        <p>${date}</p>
        <span>
          <a href="#"><i class="ri-share-fill"></i></a>
        </span>
      </div>
    </div>
  `;

  journalsGrid.appendChild(journalCard);
  journalUploadForm.reset();
  journalForm.style.display = "none";
});

const chatInput = document.getElementById("chatInput");
const sendBtn = document.getElementById("sendBtn");
const chatModal = document.getElementById("chatModal");
const chatAnswer = document.getElementById("chatAnswer");
const closeModal = document.querySelector(".chat-modal-close");

sendBtn.addEventListener("click", async () => {
  const question = chatInput.value.trim();
  if (!question) return alert("Please enter a question!");

  chatAnswer.textContent = "Thinking...";

  try {
    const response = await fetch("https://your-api-endpoint.com/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question })
    });

    const data = await response.json();
    chatAnswer.textContent = data.answer || "No answer found.";
  } catch (error) {
    chatAnswer.textContent = "Oops! Something went wrong.";
  }

  chatModal.style.display = "block";
});

closeModal.addEventListener("click", () => {
  chatModal.style.display = "none";
});

// Optional: close modal when clicking outside
window.addEventListener("click", (e) => {
  if (e.target == chatModal) {
    chatModal.style.display = "none";
  }
});
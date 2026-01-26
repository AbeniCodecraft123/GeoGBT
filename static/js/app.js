const sendBtn = document.querySelector('.send-btn');
const textarea = document.querySelector('textarea');

sendBtn.addEventListener('click', () => {
  if (textarea.value.trim() === '') {
    alert('Ask GeoAI a question first.');
    return;
  }

  alert('GeoAI response will appear here later.');
  textarea.value = '';
});
const usernameEl = document.getElementById("username");
const historyList = document.getElementById("history");
const sendBtn = document.getElementById("sendBtn");
const question = document.getElementById("question");
const logoutBtn = document.querySelector(".logout");

// Fake auth
let user = localStorage.getItem("geoai_user");

if (!user) {
  const name = prompt("Enter your name to continue:");
  if (!name) {
    window.location.href = "index.html";
  }
  localStorage.setItem("geoai_user", name);
  user = name;
}

usernameEl.textContent = user;
loadHistory();

sendBtn.onclick = () => {
  if (question.value.trim() === "") return;
  saveHistory(question.value);
  question.value = "";
};

logoutBtn.onclick = () => {
  localStorage.removeItem("geoai_user");
  window.location.href = "index.html";
};

function saveHistory(text) {
  let history = JSON.parse(localStorage.getItem("geoai_history")) || [];
  history.unshift(text);
  localStorage.setItem("geoai_history", JSON.stringify(history));
  loadHistory();
}

function loadHistory() {
  historyList.innerHTML = "";
  let history = JSON.parse(localStorage.getItem("geoai_history")) || [];
  history.slice(0, 10).forEach(h => {
    const li = document.createElement("li");
    li.textContent = h;
    historyList.appendChild(li);
  });
}


const attachBtn = document.getElementById("attachBtn");
const attachMenu = document.getElementById("attachMenu");

// Toggle menu
attachBtn.onclick = (e) => {
  e.stopPropagation(); // prevent closing immediately
  attachMenu.style.display =
    attachMenu.style.display === "block" ? "none" : "block";
};

// Close menu if click outside
document.addEventListener("click", () => {
  attachMenu.style.display = "none";
});

// Prevent click inside menu from closing it
attachMenu.addEventListener("click", (e) => {
  e.stopPropagation();
});

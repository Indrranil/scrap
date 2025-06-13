const API_BASE_URL = "http://localhost:8000/v1";  // <-- your backend URL here
let accessToken = null;

function signIn() {
  const username = document.getElementById("username").value;
  const password = document.getElementById("password").value;

  fetch(`${API_BASE_URL}/auth/signin`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password })
  })
    .then(response => {
      if (!response.ok) throw new Error("Login failed");
      return response.json();
    })
    .then(data => {
      accessToken = data.access_token;
      document.getElementById("responseArea").textContent = JSON.stringify(data, null, 2);
      console.log("Token stored:", accessToken);
    })
    .catch(error => {
      document.getElementById("responseArea").textContent = error;
    });
}

function callProtectedEndpoint() {
  if (!accessToken) {
    alert("Please sign in first!");
    return;
  }

  fetch(`${API_BASE_URL}/pipeline-session/all`, {
    headers: {
      "Authorization": `Bearer ${accessToken}`
    }
  })
    .then(response => {
      if (!response.ok) throw new Error("Failed to fetch endpoint");
      return response.json();
    })
    .then(data => {
      document.getElementById("responseArea").textContent = JSON.stringify(data, null, 2);
    })
    .catch(error => {
      document.getElementById("responseArea").textContent = error;
    });
}

function getToken() {
    return localStorage.getItem("erel_token");
}

function setToken(token) {
    localStorage.setItem("erel_token", token);
}

function logout() {
    localStorage.removeItem("erel_token");
    location.href = "/";
}

async function register() {
    const name = document.getElementById("reg-name").value;
    const username = document.getElementById("reg-username").value;
    const password = document.getElementById("reg-password").value;
    const role = document.getElementById("reg-role").value;

    const response = await fetch("/users/register", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            name: name,
            username: username,
            password: password,
            role: role
        })
    });

    const data = await response.json();

    document.getElementById("register-result").innerText = response.ok
        ? `Пользователь создан: ${data.name}`
        : data.detail || "Ошибка";
}

async function login() {
    const username = document.getElementById("login-username").value;
    const password = document.getElementById("login-password").value;

    const response = await fetch("/users/login", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            username: username,
            password: password
        })
    });

    const data = await response.json();

    if (response.ok) {
        setToken(data.token);
        document.getElementById("login-result").innerText =
            `Вы вошли как ${data.user.name}`;
                await loadProfile();
    } else {
        document.getElementById("login-result").innerText =
            data.detail || "Ошибка";
    }
}

async function loadProfile() {
    const message = document.getElementById("profile-message");
    const details = document.getElementById("profile-details");

    // На других страницах карточки профиля нет.
    if (!message || !details) {
        return;
    }

    details.hidden = true;
    message.hidden = false;

    const token = getToken();

    if (!token) {
        message.textContent = "Войдите, чтобы увидеть свой профиль.";
        return;
    }

    message.textContent = "Загрузка профиля...";

    try {
        const response = await fetch("/users/me", {
            headers: {
                token: token
            }
        });

        const user = await response.json();

        if (!response.ok) {
            if (response.status === 401) {
                localStorage.removeItem("erel_token");
            }

            throw new Error(
                typeof user.detail === "string"
                    ? user.detail
                    : "Не удалось загрузить профиль. Войдите заново."
            );
        }

        document.getElementById("profile-name").textContent = user.name;
        document.getElementById("profile-id").textContent = user.id;

        document.getElementById("profile-role").textContent =
            user.role === "staff" ? "Сотрудник" : "Ученик";

        document.getElementById("profile-balance").textContent =
            user.balance;

        document.getElementById("profile-completed").textContent =
            user.completed_tasks;

        message.hidden = true;
        details.hidden = false;
    } catch (error) {
        message.textContent = error.message;
    }
}

function taskErrorMessage(data) {
    if (typeof data.detail === "string") {
        return data.detail;
    }

    if (Array.isArray(data.detail)) {
        return data.detail.map(error => {
            const field = (error.loc || []).join(".");
            return `${field}: ${error.msg}`;
        }).join("\n");
    }

    return "Не удалось выполнить запрос.";
}


async function taskRequest(url, method = "GET", body = null) {
    const headers = {};
    const token = getToken();

    if (token) {
        headers.token = token;
    }

    if (body !== null) {
        headers["Content-Type"] = "application/json";
    }

    const response = await fetch(url, {
        method,
        headers,
        body: body === null ? undefined : JSON.stringify(body)
    });

    const data = await response.json().catch(() => ({}));

    if (!response.ok) {
        throw new Error(taskErrorMessage(data));
    }

    return data;
}


async function createTask() {
    const result = document.getElementById("task-result");

    try {
        const title = document.getElementById("task-title").value.trim();
        const description =
            document.getElementById("task-description").value.trim();
        const reward =
            Number(document.getElementById("task-reward").value);

        if (!title || !description) {
            throw new Error("Заполните название и описание.");
        }

        if (!Number.isInteger(reward) || reward <= 0) {
            throw new Error("Награда должна быть целым числом больше нуля.");
        }

        if (!getToken()) {
            throw new Error("Сначала войдите как сотрудник на главной странице.");
        }

        await taskRequest("/tasks/", "POST", {
            title,
            description,
            reward
        });

        result.textContent = "Поручение создано.";

        document.getElementById("task-title").value = "";
        document.getElementById("task-description").value = "";
        document.getElementById("task-reward").value = "";

        await loadTasks();
    } catch (error) {
        result.textContent = error.message;
    }
}


async function loadTasks() {
    const container = document.getElementById("tasks");

    if (!container) {
        return;
    }

    container.textContent = "Загрузка...";

    try {
        const tasks = await taskRequest("/tasks/");

        let currentUser = null;

        if (getToken()) {
            try {
                currentUser = await taskRequest("/users/me");
            } catch {
                currentUser = null;
            }
        }

        container.replaceChildren();

        if (tasks.length === 0) {
            container.textContent = "Поручений пока нет.";
            return;
        }

        const statuses = {
            open: "Свободно",
            in_progress: "В работе",
            completed: "Выполнено"
        };

        for (const task of tasks) {
            const card = document.createElement("div");
            card.className = "task";

            const title = document.createElement("h3");
            title.textContent = task.title;
            card.appendChild(title);

            const lines = [
                task.description,
                `Награда: ${task.reward} РЛИ-коинов`,
                `Статус: ${statuses[task.status] || task.status}`,
                `Автор: ID ${task.creator_id}`
            ];

            if (task.assignee_id !== null) {
                lines.push(`Исполнитель: ID ${task.assignee_id}`);
            }

            for (const line of lines) {
                const paragraph = document.createElement("p");
                paragraph.textContent = line;
                card.appendChild(paragraph);
            }

            if (
                currentUser &&
                currentUser.role === "student" &&
                task.status === "open"
            ) {
                const button = document.createElement("button");
                button.textContent = "Взять задание";
                button.onclick = () => takeTask(task.id);
                card.appendChild(button);
            }

            if (
                currentUser &&
                currentUser.role === "staff" &&
                currentUser.id === task.creator_id &&
                task.status === "in_progress"
            ) {
                const button = document.createElement("button");
                button.textContent = "Подтвердить и начислить награду";
                button.onclick = () => completeTask(task.id);
                card.appendChild(button);
            }

            if (
                currentUser &&
                task.assignee_id === currentUser.id &&
                task.status === "in_progress"
            ) {
                const note = document.createElement("p");
                note.textContent =
                    "Вы выполняете это поручение. После выполнения попросите автора подтвердить его.";
                card.appendChild(note);
            }

            container.appendChild(card);
        }
    } catch (error) {
        container.textContent = error.message;
    }
}


async function takeTask(taskId) {
    try {
        await taskRequest(`/tasks/${taskId}/take`, "POST");
        await loadTasks();
    } catch (error) {
        alert(error.message);
    }
}


async function completeTask(taskId) {
    try {
        await taskRequest(`/tasks/${taskId}/complete`, "POST");
        await loadTasks();
        alert("Выполнение подтверждено. Ученику начислена награда.");
    } catch (error) {
        alert(error.message);
    }
}
async function transferMoney() {
    const toUserId = Number(document.getElementById("to-user").value);
    const amount = Number(document.getElementById("amount").value);
    const token = getToken();

    const response = await fetch("/bank/transfer", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "token": token
        },
        body: JSON.stringify({
            to_user_id: toUserId,
            amount: amount
        })
    });

    const data = await response.json();

    document.getElementById("transfer-result").innerText = response.ok
        ? "Перевод выполнен"
        : data.detail || "Ошибка";
}

async function createAuction() {
    const itemName = document.getElementById("item-name").value;
    const startPrice = Number(document.getElementById("start-price").value);
    const token = getToken();

    const response = await fetch("/bank/auctions/", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "token": token
        },
        body: JSON.stringify({
            item_name: itemName,
            start_price: startPrice
        })
    });

    const data = await response.json();

    document.getElementById("auction-result").innerText = response.ok
        ? `Лот создан: ${data.item_name}`
        : data.detail || "Ошибка";

    if (response.ok) {
        loadAuctions();
    }
}

async function loadAuctions() {
    const response = await fetch("/bank/auctions/");
    const lots = await response.json();
    const token = getToken();

    const container = document.getElementById("auctions");

    if (!container) {
        return;
    }

    container.innerHTML = "";

    if (lots.length === 0) {
        container.innerHTML = "<p>Лотов пока нет.</p>";
        return;
    }

    lots.forEach(lot => {
        const div = document.createElement("div");
        div.className = "auction";

        let buttons = "";

        if (token && lot.is_active && !lot.is_sold) {
            buttons += `
                <input
                    type="number"
                    id="bid-${lot.id}"
                    placeholder="Твоя ставка"
                >
                <button onclick="placeBid(${lot.id})">
                    Сделать ставку
                </button>
                <button onclick="closeAuction(${lot.id})">
                    Завершить аукцион
                </button>
            `;
        }

        if (token && !lot.is_active && !lot.is_sold) {
            buttons += `
                <button onclick="buyLot(${lot.id})">
                    Купить лот
                </button>
            `;
        }

        let status = "Аукцион активен";

        if (lot.is_sold) {
            status = "Лот продан";
        } else if (!lot.is_active) {
            status = "Аукцион завершён";
        }

        div.innerHTML = `
            <strong>${lot.item_name}</strong>
            <p>Текущая цена: ${lot.current_bid} РЛИ-коинов</p>
            <p>Статус: ${status}</p>
            ${buttons}
        `;

        container.appendChild(div);
    });
}

async function placeBid(lotId) {
    const bidAmount = Number(
        document.getElementById(`bid-${lotId}`).value
    );
    const token = getToken();

    const response = await fetch(
        `/bank/auctions/${lotId}/bid?bid_amount=${bidAmount}`,
        {
            method: "POST",
            headers: {
                "token": token
            }
        }
    );

    const data = await response.json();

    if (response.ok) {
        loadAuctions();
    } else {
        alert(data.detail || "Ошибка");
    }
}

async function closeAuction(lotId) {
    const token = getToken();

    const response = await fetch(`/bank/auctions/${lotId}/close`, {
        method: "POST",
        headers: {
            "token": token
        }
    });

    const data = await response.json();

    if (response.ok) {
        loadAuctions();
    } else {
        alert(data.detail || "Ошибка");
    }
}

async function buyLot(lotId) {
    const token = getToken();

    const response = await fetch(`/bank/auctions/${lotId}/buy`, {
        method: "POST",
        headers: {
            "token": token
        }
    });

    const data = await response.json();

    if (response.ok) {
        loadAuctions();
    } else {
        alert(data.detail || "Ошибка");
    }
}

loadTasks();
loadAuctions();
if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", loadProfile);
} else {
    loadProfile();
}
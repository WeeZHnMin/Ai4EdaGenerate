const form = document.getElementById("generate-form");
const promptInput = document.getElementById("prompt");
const submitBtn = document.getElementById("submit-btn");
const statusText = document.getElementById("status-text");
const resultMessage = document.getElementById("result-message");
const resultImage = document.getElementById("result-image");
const modelStatus = document.getElementById("model-status");

let serviceReady = false;

async function refreshStatus() {
  try {
    const response = await fetch("/api/status");
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    const data = await response.json();
    modelStatus.textContent = data.message;

    if (data.status === "ready") {
      serviceReady = true;
      submitBtn.disabled = false;
      statusText.textContent = "模型已就绪。";
      return;
    }

    serviceReady = false;
    submitBtn.disabled = true;
    statusText.textContent = data.status === "loading" ? "模型加载中..." : "模型不可用。";
  } catch (error) {
    console.error(error);
    serviceReady = false;
    submitBtn.disabled = true;
    modelStatus.textContent = "无法获取模型状态，请检查后端服务。";
    statusText.textContent = "后端连接失败。";
  }
}

refreshStatus();
setInterval(refreshStatus, 3000);

form.addEventListener("submit", async (event) => {
  event.preventDefault();

  if (!serviceReady) {
    statusText.textContent = "模型尚未就绪，请稍后再试。";
    return;
  }

  const prompt = promptInput.value.trim();
  if (!prompt) {
    statusText.textContent = "请输入提示词。";
    promptInput.focus();
    return;
  }

  submitBtn.disabled = true;
  statusText.textContent = "正在生成图片...";
  resultMessage.textContent = "后端处理中。";

  try {
    const response = await fetch("/api/generate", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ prompt }),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || `HTTP ${response.status}`);
    }

    const data = await response.json();
    resultImage.src = `data:image/png;base64,${data.image_base64}`;
    resultImage.hidden = false;
    resultMessage.textContent = `${data.message} 当前功能：${data.function}`;
    statusText.textContent = "生成完成。";
  } catch (error) {
    console.error(error);
    statusText.textContent = "生成失败。";
    resultMessage.textContent = `请求出错：${error.message}`;
    resultImage.hidden = true;
  } finally {
    submitBtn.disabled = !serviceReady;
  }
});

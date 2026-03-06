const form = document.getElementById("generate-form");
const promptInput = document.getElementById("prompt");
const submitBtn = document.getElementById("submit-btn");
const statusText = document.getElementById("status-text");
const resultMessage = document.getElementById("result-message");
const resultImage = document.getElementById("result-image");

form.addEventListener("submit", async (event) => {
  event.preventDefault();

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
      throw new Error(`HTTP ${response.status}`);
    }

    const data = await response.json();
    resultImage.src = `data:image/png;base64,${data.image_base64}`;
    resultImage.hidden = false;
    resultMessage.textContent = `${data.message} 当前展示功能：${data.function}`;
    statusText.textContent = "生成完成。";
  } catch (error) {
    console.error(error);
    statusText.textContent = "生成失败。";
    resultMessage.textContent = "请求出错，请检查后端服务是否正常。";
    resultImage.hidden = true;
  } finally {
    submitBtn.disabled = false;
  }
});

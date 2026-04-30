const form = document.querySelector("#refineForm");
const fileInput = document.querySelector("#fileInput");
const fileChip = document.querySelector("#fileChip");
const fileName = document.querySelector("#fileName");
const clearFile = document.querySelector("#clearFile");
const textInput = document.querySelector("#textInput");
const roundInput = document.querySelector("#refineRounds");
const roundOutput = document.querySelector("#roundOutput");
const realConfig = document.querySelector("#realConfig");
const statusPill = document.querySelector("#statusPill span:last-child");
const progressRail = document.querySelector("#progressRail");
const markdownOutput = document.querySelector("#markdownOutput");
const jsonOutput = document.querySelector("#jsonOutput");
const copyMarkdown = document.querySelector("#copyMarkdown");
const downloadJson = document.querySelector("#downloadJson");

let latestJson = null;

roundInput.addEventListener("input", () => {
  roundOutput.value = roundInput.value;
  roundOutput.textContent = roundInput.value;
});

document.querySelectorAll("input[name='provider']").forEach((input) => {
  input.addEventListener("change", () => {
    realConfig.classList.toggle("open", input.value === "real" && input.checked);
  });
});

fileInput.addEventListener("change", () => {
  const file = fileInput.files[0];
  fileChip.hidden = !file;
  fileName.textContent = file ? file.name : "未选择文件";
});

clearFile.addEventListener("click", () => {
  fileInput.value = "";
  fileChip.hidden = true;
  fileName.textContent = "未选择文件";
});

document.querySelectorAll(".tab").forEach((tab) => {
  tab.addEventListener("click", () => {
    document.querySelectorAll(".tab").forEach((item) => item.classList.remove("active"));
    document.querySelectorAll(".result-view").forEach((item) => item.classList.remove("active"));
    tab.classList.add("active");
    document.querySelector(`#${tab.dataset.tab}View`).classList.add("active");
  });
});

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  setBusy(true);

  const body = new FormData(form);
  if (!fileInput.files.length) {
    body.delete("file");
    body.set("text", textInput.value);
  }

  try {
    const response = await fetch("/api/refine", {
      method: "POST",
      body,
    });
    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.error || "转换失败");
    }
    latestJson = payload.data;
    markdownOutput.textContent = payload.markdown;
    jsonOutput.textContent = JSON.stringify(payload.data, null, 2);
    statusPill.textContent = "Converted";
  } catch (error) {
    statusPill.textContent = "Error";
    markdownOutput.textContent = error.message;
    jsonOutput.textContent = "{}";
  } finally {
    setBusy(false);
  }
});

copyMarkdown.addEventListener("click", async () => {
  await navigator.clipboard.writeText(markdownOutput.textContent);
  statusPill.textContent = "Copied";
});

downloadJson.addEventListener("click", () => {
  if (!latestJson) {
    return;
  }
  const blob = new Blob([JSON.stringify(latestJson, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = `textrefine-${latestJson.mode || "result"}.json`;
  anchor.click();
  URL.revokeObjectURL(url);
});

function setBusy(isBusy) {
  const button = form.querySelector(".primary-action");
  button.disabled = isBusy;
  button.textContent = isBusy ? "转换中..." : "开始转换";
  progressRail.classList.toggle("running", isBusy);
  if (isBusy) {
    statusPill.textContent = "Working";
  }
}

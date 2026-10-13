(function () {
  "use strict";

  function highlightBibTeX(code, source) {
    source.split("\n").forEach(function (line, index, lines) {
      var type = line.match(/^(@[a-z]+)/i);
      var value = line.match(/^(\s*[a-z][a-z-]*\s*=\s*)(\{.*\})(,?)$/i);
      if (type) {
        var typeSpan = document.createElement("span");
        typeSpan.className = "bibtex-type";
        typeSpan.textContent = type[1];
        code.appendChild(typeSpan);
        code.appendChild(document.createTextNode(line.slice(type[1].length)));
      } else if (value) {
        code.appendChild(document.createTextNode(value[1]));
        var valueSpan = document.createElement("span");
        valueSpan.className = "bibtex-value";
        valueSpan.textContent = value[2];
        code.appendChild(valueSpan);
        code.appendChild(document.createTextNode(value[3]));
      } else {
        code.appendChild(document.createTextNode(line));
      }
      if (index < lines.length - 1) code.appendChild(document.createTextNode("\n"));
    });
  }

  function initBibTeX() {
    var dataElement = document.getElementById("publication-bibtex-data");
    if (!dataElement) return;
    var citations;
    try {
      citations = JSON.parse(dataElement.textContent);
    } catch (error) {
      console.error("Unable to read publication citations", error);
      return;
    }
    var activeButton = null;

    document.querySelectorAll(".bibtex-toggle").forEach(function (button) {
      var key = button.dataset.bibtexKey;
      var citation = citations[key];
      var item = button.closest("li");
      if (!citation || !citation.bibtex || !item) return;

      var panel = document.createElement("div");
      panel.id = "bibtex-" + key;
      panel.className = "bibtex-panel";
      panel.hidden = true;
      panel.setAttribute("role", "region");
      panel.setAttribute("aria-label", "BibTeX citation for " + citation.title);

      var toolbar = document.createElement("div");
      toolbar.className = "bibtex-toolbar";
      var label = document.createElement("span");
      label.className = "bibtex-label";
      label.textContent = "BibTeX";
      var copy = document.createElement("button");
      copy.type = "button";
      copy.className = "bibtex-copy";
      copy.textContent = "Copy BibTeX";
      var status = document.createElement("span");
      status.className = "bibtex-status";
      status.setAttribute("role", "status");
      status.setAttribute("aria-live", "polite");
      toolbar.appendChild(label);
      toolbar.appendChild(copy);
      toolbar.appendChild(status);

      var pre = document.createElement("pre");
      var code = document.createElement("code");
      highlightBibTeX(code, citation.bibtex);
      pre.appendChild(code);
      panel.appendChild(toolbar);
      panel.appendChild(pre);
      item.appendChild(panel);
      button.setAttribute("aria-controls", panel.id);
      button.hidden = false;

      button.addEventListener("click", function () {
        var opening = button.getAttribute("aria-expanded") !== "true";
        if (activeButton && activeButton !== button) {
          activeButton.setAttribute("aria-expanded", "false");
          activeButton.setAttribute("aria-label", "Show BibTeX citation");
          document.getElementById(activeButton.getAttribute("aria-controls")).hidden = true;
        }
        panel.hidden = !opening;
        button.setAttribute("aria-expanded", String(opening));
        button.setAttribute("aria-label", (opening ? "Hide" : "Show") + " BibTeX citation");
        activeButton = opening ? button : null;
        status.textContent = "";
      });

      copy.addEventListener("click", async function () {
        try {
          if (!navigator.clipboard || !navigator.clipboard.writeText) throw new Error("Clipboard unavailable");
          await navigator.clipboard.writeText(citation.bibtex);
          status.textContent = "Copied!";
        } catch (error) {
          var range = document.createRange();
          range.selectNodeContents(code);
          var selection = window.getSelection();
          if (selection) {
            selection.removeAllRanges();
            selection.addRange(range);
          }
          status.textContent = "Select and copy with Ctrl+C / ⌘C";
        }
      });
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initBibTeX);
  } else {
    initBibTeX();
  }
})();

(function () {
  function clearQuiz(root) {
    root.querySelectorAll(".mb-q").forEach(function (q) {
      q.classList.remove("is-correct", "is-wrong", "is-blank");
      q.querySelectorAll("label").forEach(function (label) {
        label.classList.remove("is-key");
      });
      q.querySelectorAll("input").forEach(function (input) {
        input.checked = false;
      });
      var why = q.querySelector(".mb-q-why");
      if (why) why.hidden = true;
    });
    var score = root.querySelector(".mb-quiz-score");
    if (score) score.textContent = "";
  }

  function gradeQuiz(root) {
    var questions = root.querySelectorAll(".mb-q");
    var correct = 0;
    questions.forEach(function (q) {
      var answer = q.getAttribute("data-answer");
      var picked = q.querySelector("input:checked");
      q.classList.remove("is-correct", "is-wrong", "is-blank");
      q.querySelectorAll("label").forEach(function (label) {
        label.classList.remove("is-key");
      });
      var key = q.querySelector('input[value="' + answer + '"]');
      if (key && key.parentElement) key.parentElement.classList.add("is-key");
      var why = q.querySelector(".mb-q-why");
      if (why) why.hidden = false;
      if (!picked) {
        q.classList.add("is-blank");
        return;
      }
      if (picked.value === answer) {
        correct += 1;
        q.classList.add("is-correct");
      } else {
        q.classList.add("is-wrong");
      }
    });
    var score = root.querySelector(".mb-quiz-score");
    if (!score) return;
    var total = questions.length;
    if (correct === total) {
      score.textContent = correct + " / " + total + ". Close the notes and say the memorize list once from memory.";
    } else {
      score.textContent = correct + " / " + total + ". Green is correct, amber is a miss, gray was left blank. The marked choice is the key.";
    }
  }

  document.querySelectorAll("[data-mb-quiz]").forEach(function (root) {
    var check = root.querySelector(".mb-quiz-check");
    var reset = root.querySelector(".mb-quiz-reset");
    if (check) check.addEventListener("click", function () { gradeQuiz(root); });
    if (reset) reset.addEventListener("click", function () { clearQuiz(root); });
  });
})();

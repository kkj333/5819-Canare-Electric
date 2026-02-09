/* TOC sidebar: scroll-spy + hamburger toggle */
(function () {
  "use strict";

  var sidebar = document.querySelector(".toc-sidebar");
  var toggle = document.querySelector(".toc-toggle");
  var overlay = document.querySelector(".toc-overlay");
  if (!sidebar) return;

  /* --- Smooth scroll & mobile close --- */
  sidebar.addEventListener("click", function (e) {
    var link = e.target.closest("a");
    if (!link) return;
    e.preventDefault();
    var target = document.querySelector(link.getAttribute("href"));
    if (target) target.scrollIntoView({ behavior: "smooth" });
    closeSidebar();
  });

  /* --- Hamburger toggle --- */
  function openSidebar() {
    sidebar.classList.add("open");
    if (overlay) overlay.classList.add("open");
  }
  function closeSidebar() {
    sidebar.classList.remove("open");
    if (overlay) overlay.classList.remove("open");
  }
  if (toggle) toggle.addEventListener("click", function () {
    sidebar.classList.contains("open") ? closeSidebar() : openSidebar();
  });
  if (overlay) overlay.addEventListener("click", closeSidebar);

  /* --- IntersectionObserver scroll-spy --- */
  var headings = document.querySelectorAll(".report-content h2, .report-content h3");
  var tocLinks = sidebar.querySelectorAll("a");
  if (!headings.length || !tocLinks.length) return;

  var linkMap = {};
  tocLinks.forEach(function (a) { linkMap[a.getAttribute("href").slice(1)] = a; });

  var observer = new IntersectionObserver(function (entries) {
    entries.forEach(function (entry) {
      if (entry.isIntersecting) {
        tocLinks.forEach(function (a) { a.classList.remove("active"); });
        var a = linkMap[entry.target.id];
        if (a) a.classList.add("active");
      }
    });
  }, { rootMargin: "0px 0px -60% 0px", threshold: 0 });

  headings.forEach(function (h) { observer.observe(h); });
})();

// Script to add loading bars to cards with headers using the title's percentage metric (always assumed to exist)
// 
// chars: █▒

function getCharacterWidth() {
    let span = document.createElement("span");
    span.style.position = "absolute";
    span.style.visibility = "hidden";
    // apparently chars can have non-integer pixel width, so use multiple and take the average
    span.textContent = "▒▒▒▒▒▒▒▒▒▒";
    document.body.appendChild(span);
    let characterWidth = span.offsetWidth / 10;
    document.body.removeChild(span);
    return characterWidth;
}


function createLoadingBar(width, percentage) {
   let loadingBar = "";
   for (let i = 0; i < width; i++) {
       if (i < width * percentage / 100) {
           loadingBar += "█";
       } else {
           loadingBar += "▒";
       }
   }
   return loadingBar;
}

window.addEventListener("resize", () => {
   let cards = document.querySelectorAll(".sd-card");
   let characterWidth = getCharacterWidth();
   cards.forEach(card => {
     let header = card.querySelector(".sd-card-header p");
     if (!card.contains(header)) {
     		return;
     }
     let percentageSpan = card.querySelector(".sd-card-title span");
     let percentage = parseFloat(percentageSpan.textContent); // parseFloat takes care of the trailing "%"
     let headerWidth = header.offsetWidth;
     let headerWidthInChars = Math.floor(headerWidth / characterWidth);
     let loadingBar = createLoadingBar(headerWidthInChars, percentage);
     header.textContent = loadingBar;
   });
});


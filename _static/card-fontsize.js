window.addEventListener('resize', function() {
 let cardFontMultiplier = 3;

 var cardBodyDivs = document.querySelectorAll('.sd-card-body');
 
 cardBodyDivs.forEach(function(div) {
  var p = div.querySelector('p');
  var pFontSize = parseFloat(window.getComputedStyle(p, null).getPropertyValue('font-size'));
 
  let titleDiv = div.querySelector(".sd-card-title");
  let title = div.querySelector(".sd-card-title span")
  if (title === null) {
   title = titleDiv
  }
  title.style.fontSize = (pFontSize * cardFontMultiplier) + 'px';
 });
});


//Get the Accordion Groups
const accordions = document.querySelectorAll(".accordion");


accordions.forEach(accordion => {
  //Add event listener to each ACCORDION , use function not fat arrow to get access to "this"
  accordion.addEventListener("click", function(event) {
    //Check the event targe is an item header
    if (event.target.matches(".accordion-item-header")) {
      //Get current active, here "this" refers to the accordion group clicked on
      let active = this.querySelector(".active");
      
      //Toggle element if active element clicked
      if (active == event.target) {
        event.target.classList.toggle("active");
      } else {
        //Remove current active.
        if (active) {
          active.classList.remove("active");
        }
        //Add active        
        event.target.classList.add("active");
      }
    }
  });
});



var user = JSON.parse('{{ user | tojson | safe}}');
console.log(user)

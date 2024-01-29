const intro = introJs();

intro.setOptions({
    steps: [
        {
            element: '#documents',
            intro: 'This is how you get back to the list of documents'
        },
        {
            element: '#model_suggestion',
            intro: 'The AI model will analyze your existing labels and provide suggestions based on them. It will propose labels that it believes are relevant for the current passage, drawing from the labels you have previously created.'
        },
        {
            element: '#model_sugges',
            intro: "Label the passage by either typing a custom label or selecting from your previously created labels in the dropdown. Aim to create labels that are sufficiently general, allowing them to be applied to as many passages as possible with similar themes"
        },
        {
            element: '#myBtn',
            intro: 'Submits your label and takes you to the next AI recommended document. Remember you can always go back to the document list page'
        },
        {
            element: '#topic11',
            intro: 'In this block, you will find potential topics associated with the passage, ranked by relevance. These word clusters can also serve as potential label ideas for the passage'
        },
        {
            element: '#buttons',
            intro: 'Highlights important words that can help you identify the label for the passage'
        },
        {
            element: '#extraBtn',
            intro: 'Skip the current document and takes you to the next AI recommended document. If you think the tool recommends you passages with the same theme too often, skip the document to avoid model overfit'
        },
        {
            element: '#completed',
            intro: 'A \'View/Edit Response\' button appears after labeling one document. This display your labeled documents'
        },
        {
            element: '#demo',
            intro: 'Click this button if you want to go through this demo again'
        }
    ]
})

const hasRunIntro = localStorage.getItem("hasRunIntro");
if (hasRunIntro !== "1"){
    intro.start();
    localStorage.setItem("hasRunIntro", "1");
}
document.getElementById("demo").addEventListener('click', function(){
    intro.start();

})


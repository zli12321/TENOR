const intro = introJs();

intro.setOptions({
    steps: [
        {
            intro: "This demo will walk you through how to use this tool"
        },
        
        {
            element: '#home',
            intro: 'This takes you to the previous page with instructions'
        },
        {
            element: '#completed',
            intro: 'A \'View/Edit Response\' button will appear on the top navigation bar after labelling one document. This displays your labeled documents, and you can edit your labels for the labeled documents'
        },
        {
            element: '#act_lis',
            intro: 'This is the list of documents to label. You can click one of the documents to start labeling'
        },
        {
            element: '#recommended',
            intro: 'The red text is an AI recommended document to label'
        },
        {
            element: "#sessionTimer",
            intro: 'The timer shows you the elapsed time. Once you reached the time and created a good set of labels, you can finish and take the survey'
        },
        {
            element: "#finish",
            intro: 'Click here to finish the study and take the survey'
        },
        {
            element: '#demo',
            intro: 'Click this button if you want to go through this demo again'
        }
    
    ]
})

// const hasRunIntro = localStorage.getItem("hasRunIntro");
// if (hasRunIntro !== "1"){
//     intro.start();
//     localStorage.setItem("hasRunIntro", "1");
// }
document.getElementById("demo").addEventListener('click', function(){
    intro.start();

})

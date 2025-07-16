
let folderTree = null;

function loadFolderTree(){
    // Show the loading indicator
    document.getElementById('loading_indicator').style.display = 'block';

    // Clear any existing trees
    if (folderTree) {
        document.getElementById('folder_tree_container').innerHTML = '';
    }

    // Fetch the folder structure as JSON
    fetch(`/api/infrastructure/tree`)
        .then(response => {
            if (!response.ok) {
                throw new Error(`Error ${response.status}: ${response.statusText}`);
            }
            return response.json();
        })
        .then(responseData => {
            if (!responseData.success) {
                throw new Error(responseData.message || responseData.error || 'Unknown error occurred');
            }
            initializeFolderTree(responseData.data);
            document.getElementById('loading_indicator').style.display = 'none';

        })
        .catch(error => {
            console.error('Error fetching tree data:', error);
            document.getElementById('loading_indicator').style.display = 'none';
            alert('Error loading folder structure. Please update .flaskenv again with a readable directory');
        })
}

function initializeFolderTree(treeData){
   // First, destroy any existing trees to prevent duplicates
    if ($('#folder_tree_container').hasClass('jstree')) {
        $('#folder_tree_container').jstree('destroy');
    }
    // Initialize jsTree
    $(function () {
        $('#folder_tree_container').jstree({
            'core': {
                data: treeData,
            },
            'plugins': ['search', 'types'],
            'types': {
                'folder': {
                    'li_attr': {'class': 'folder-node'}
                },
                'file': {
                    'li_attr': {'class': 'file-node'},
                    'icon': 'bi bi-file'
                }
            }
        });
    });
    $('#folder_tree_container').on('ready.jstree', function() {
        const tree = $('#folder_tree_container').jstree(true);

        // Override default click behavior
        $('#folder_tree_container').on('select_node.jstree', function(e, data) {
            // Prevent selection of file nodes
            if (data.node.type === 'file') {
                e.preventDefault();
                e.stopPropagation();
                tree.deselect_node(data.node);
                return false;
            }
        });
    });

    $('#folder_tree_container').on('changed.jstree', function(e, data) {
        handleFolderPathSelection(treeData)
    });
}

function handleFolderPathSelection(){
    const tree = $('#folder_tree_container').jstree(true);
    const selectedId = tree.get_selected();

    if (selectedId.length === 0){
        $('#samples_inside_folder_indicator').attr('style', 'display: none !important;');
    } else{
        $('#samples_inside_folder_indicator').css('display', 'block')

        const selectedNode = tree.get_node(selectedId[0]);
        const path = selectedNode.original.path;


        retrievePreliminarySamples(path)
        setFolderFormInputs(path)
    }
}

function setFolderFormInputs(path){
    let folderModalityPathInput = document.querySelector('input[name="folder_modality_path"]');

    // Check if the input exists; if not, create it
    if (!folderModalityPathInput) {
        folderModalityPathInput = document.createElement('input');
        folderModalityPathInput.type = 'hidden';
        folderModalityPathInput.name = 'folder_modality_path';
        document.getElementById('new-session-form').appendChild(folderModalityPathInput);
    }

    // Set the value
    folderModalityPathInput.value = path;
}

function retrievePreliminarySamples(path){
    document.getElementById('loading_indicator').style.display = 'block';
    document.getElementById('samples_inside_folder_indicator').innerHTML = "";

    const encodedPath = encodeURIComponent(path);
    fetch(`/ajax/infrastructure/get_samples?path=${encodedPath}`)
        .then(response => {
            if (!response.ok) {
                throw new Error(`Error ${response.status}: ${response.statusText}`);
            }
            return response.json();
        })
        .then(data => {
            const files_found_div = `<div>${data.count} files found</div>`;
            document.getElementById('samples_inside_folder_indicator').innerHTML = files_found_div;
            document.getElementById('loading_indicator').style.display = 'none';
        })
        .catch(error => {
            console.error('Error fetching samples list data:', error);
            document.getElementById('loading_indicator').style.display = 'none';
            alert('Error retrieving samples from folder. Please try again.');
        })

}

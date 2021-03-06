/* eslint-disable no-multiple-empty-lines */
/* eslint-disable no-use-before-define */
document.addEventListener('DOMContentLoaded', async () => {
  const isChrome = !!window.chrome;

  // Top search result
  let queryTopResultLink = null;
  let queryTopResultText = null;
  
  // Data for the link clicked from searched results
  let queryResultText = null;
  let queryResultLink = null;
  let voiceSearchQuery = null;
  const searchIcon = document.querySelector('#searchSVG');
  const searchMainDiv = document.querySelector('#searchMainDiv');
  const searchBox = document.querySelector('#searchInputBox');
  const searchSuggestion = document.querySelector('#searchSuggestion');
  const searchSuggestionList = document.querySelector('#searchSuggestionList');
  const mainDiv = document.querySelector('#mainDiv');
  const audioModalContentChildren = document.querySelector('#audioModalContent').children;
  const audioModal = new bootstrap.Modal(document.querySelector('#audioModal'));
  const audioModalById = document.querySelector('#audioModal');
  const audioModalHeader = document.querySelector('#audioModalHeader');
  const wikipediaAccordian = document.querySelector('#wikipediaAccordian');
  const voiceSearchModal = new bootstrap.Modal(document.querySelector('#voiceSearchModal'));
  const voiceSearchIcon = document.querySelector('#voiceSearch');
  const voiceSearchCurrentStatus = document.querySelector('#voiceSearchCurrentStatus');
  const voiceSearchResult = document.querySelector('#voiceSearchCurrentStatus');
  const spinner = document.querySelector('#spinner');
  const languageSelector = document.querySelector('#languageSelector');
  let queryLanguage = languageSelector.options[languageSelector.selectedIndex].value;
  const wikiLinksDict = {
    hi: 'https://hi.wikipedia.org/w/api.php?action=opensearch&format=json&origin=*&formatversion=2&search=',
    en: 'https://en.wikipedia.org/w/api.php?action=opensearch&format=json&origin=*&formatversion=2&search=',
  };
  const voiceSearchLanguagesDict = {
    en: 'en-US',
    hi: 'hi-IN',
  };

  if (!isChrome) {
    voiceSearchIcon.style.display = 'none';
  }



  // #############################################################################
  // ## General
  // #############################################################################



  function showSpinner() {
    spinner.style.display = 'flex';
  }

  function hideSpinner() {
    spinner.style.display = 'none';
  }



  // #############################################################################
  // ## Voice search related Functions                                          ##
  // #############################################################################




  function showVoiceSearchError(msg) {
    voiceSearchCurrentStatus.className = 'alert alert-danger';
    voiceSearchCurrentStatus.innerHTML = msg;
  }

  function showVoiceSearchNormalMsg(msg) {
    voiceSearchCurrentStatus.className = 'alert alert-light';
    voiceSearchCurrentStatus.innerHTML = msg;
  }

  function addVoiceQuery() {
    searchBox.value = voiceSearchQuery;
    showSuggestionsForQueryInInputBox(voiceSearchQuery);
  }

  voiceSearchIcon.addEventListener('click', () => {
    console.debug('voiceSearchIcon clicked');
    listenToVoiceQuery();
  });

  function getVoiceSearchLanguage() {
    return voiceSearchLanguagesDict[queryLanguage];
  }

  async function listenToVoiceQuery() {
    const listening = false;
    console.debug('inside listen to voice query');
    if (!('webkitSpeechRecognition' in window)) {
      // TODO : Show a update to chrome message or completly hide this svg
    } else {
      const recognition = await new webkitSpeechRecognition();
      // recognition.continuous = true;
      recognition.interimResults = true;
      recognition.lang = getVoiceSearchLanguage();
      console.debug(`recognition data is ${recognition}`);

      recognition.onstart = (e) => {
        showVoiceSearchNormalMsg('Listening ...');
        console.debug(`recognition started ${e}`);
      };

      recognition.onresult = (e) => {
        console.debug(`recognition complete here is your result ${e.results[0][0].transcript}`);
        console.debug(`here is your event ${e}`);
        const trans = e.results[0][0].transcript;

        console.debug(`recognition complete here is your result ${trans}`);
        voiceSearchResult.innerHTML = trans;
        voiceSearchQuery = trans;
        return trans;
      };

      recognition.onerror = (e) => {
        if (e.error === 'no-speech') {
          showVoiceSearchError('No speech was detected. You may need to adjust your  microphone');
        }
        if (e.error === 'audio-capture') {
          showVoiceSearchError('No microphone was found. Ensure that a microphone is installed and that microphone settings</a> are configured correctly.');
        }
        if (e.error === 'not-allowed') {
          showVoiceSearchError('Permission to use microphone was denied/blocked. To change,go to chrome://settings/contentExceptions#media-stream');
        }

        console.debug(` error occured : ${e.error}`);
      };
      recognition.onend = async () => {
        console.debug('ended');
        setTimeout(() => {
          showVoiceSearchNormalMsg('Closing voice search');
          voiceSearchModal.hide();
          addVoiceQuery();
        }, 3000);
      };

      recognition.start();
    }
  }



  // #############################################################################
  // ## Audio Modal for search query result
  // #############################################################################




  function showAudioModal(mediaLocation, articleText, articleWikiLink) {
    // console.debug(`media location is : ${mediaLocation} and articleText is ${articleText}`)
    const audioModalBody = audioModalContentChildren[1];
    const audioModalFooter = audioModalContentChildren[2];
    // console.debug(audioModalHeader, audioModalBody, audioModalFooter)
    audioModalHeader.innerHTML = `<audio id="audioControl" controls style="width: 100%;"><source src="${mediaLocation}" type="audio/mpeg" />Your browser does not support the audio element.</audio>`;
    audioModalBody.innerHTML = articleText;
    audioModalFooter.innerHTML = `<a href="${articleWikiLink}">${articleWikiLink}</a>`;
    audioModal.toggle();
  }

  audioModalById.addEventListener('hide.bs.modal', () => {
    console.log('modal closed');
    const audioControl = document.querySelector('#audioControl');
    audioControl.pause();
  });



  // #############################################################################
  // ## Show wikipedia article accordian
  // #############################################################################



  function createWikipediaContentLinks(wikiContentText) {
    const wikiContentTextJoined = wikiContentText.split(' ').join('_');
    const fullWikiLink = `${queryResultLink}#${wikiContentTextJoined}`;
    // console.debug(fullWikiLink)
    return fullWikiLink;
  }

  function makeArticlesList(articleText) {
    const l = ['Article Contents :', '<ul>'];
    l.push(`<li class="accordianCardLinks" 
        id='${createWikipediaContentLinks('')}'
        >Introduction
        </li>`);
    for (let i = 1; i < articleText.length; i += 1) {
      l.push(`<li class="accordianCardLinks" 
            id='${createWikipediaContentLinks(articleText[i][0])}'
            >${articleText[i][0]}
            </li>`);
    }
    l.push('</ul>');
    return l.join('');
  }

  function createNewAccordianCard(articleTitle, articleContents) {
    const articleContentsList = makeArticlesList(articleContents);
    const articleTitleForIds = articleTitle.split(' ').join('');
    const newCard = `<div class="card" style="margin-top: 20px">
        <div class="card-header" id="${articleTitleForIds}Wiki">
          <h2 class="mb-0">
            <button class="btn btn-link btn-block text-left" type="button" data-toggle="collapse" data-target="#${articleTitleForIds}collapse" aria-expanded="true" aria-controls="collapseOne">
            ${articleTitle}
            </button>
          </h2>
        </div>
    
        <div id="${articleTitleForIds}collapse" class="collapse show" aria-labelledby="${articleTitleForIds}Wiki" data-parent="#wikipediaAccordian">
          <div class="card-body">
            ${articleContentsList}
          </div>
        </div>
      </div>`;
    wikipediaAccordian.insertAdjacentHTML('afterbegin', newCard);
    //   console.debug(newCard)
  }



  // #############################################################################
  // ## Make requests
  // #############################################################################



  function getAudioFileData(functionToHandleTheResponse, articleWikiLink) {
    showSpinner();
    console.debug(`function to handle response is ${functionToHandleTheResponse}`);
    const request = new XMLHttpRequest();
    request.open('POST', '/text_to_speech/wikipedia/');
    request.onload = () => {
      hideSpinner();
      console.debug(`request response text is ${request.responseText}`);
      const data = JSON.parse(request.responseText);
      console.log(`query Text is ${queryResultText}, query Link is ${queryResultLink}`)
      if (functionToHandleTheResponse === 'showAudioModal') {
        showAudioModal(data.mediaLocation, data.txt, articleWikiLink);
      } else if (functionToHandleTheResponse === 'both') {
        showAudioModal(data.mediaLocation, data.txt, articleWikiLink);
        createNewAccordianCard(queryResultText, data.articleContents);
      }
    };
    const data = new FormData();
    data.append('wikipediaLink', articleWikiLink);
    data.append('articleLanguage', queryLanguage);
    console.debug(`sending request to text_to_speech/wikipedia with wikipediaLink ${articleWikiLink} articleLanguage ${queryLanguage}`);
    // request.setRequestHeader("Content-type", "application/json")
    request.send(data);
  }

  function matchString(s1, s2) {
    const l1 = s1.toLowerCase();
    const l2 = s2.toLowerCase();
    // console.debug(s1,'---', s2)
    if (l1 === l2) { return s2; }

    let res = '';
    for (let x = 0; x <= s1.length; x += 1) {
      if (l1[x] === l2[x]) {
        res += s2[x];
      } else {
        break;
      }
    }
    return res;
  }


  function getWikipediaresponseAsList(searchQueryText) {
    /*
     Use wikipedia search api to get results for the searchQueryText
     Wikipedia search api has format :
     https://<Insert language>.wikipedia.org/w/api.php?action=opensearch&format=json&origin=*&formatversion=2&search=<Insert search query>&namespace=0&limit=<Insert no of results to show>'

     return format for let's say "Hampi" is :
     [
      "Hampi",
      [
          "Hampi",
          ...
      ],
      [
          "Hampi, also referred to as the Group of Monuments at Hampi",
          ...
      ],
      [
          "https://en.wikipedia.org/wiki/Hampi",
          ...
      ]
    ]

    i.e [search query, [list of search results heading], [list of description for earch search heading], [list of links for each search heading]]
    */
    const wikiLink = `${wikiLinksDict[queryLanguage] + searchQueryText}&namespace=0&limit=10`;

    // Make a request to wikipedia using this link
    const request = new XMLHttpRequest();
    request.open('GET', wikiLink);

    // When result is returned
    request.onload = () => {
      const data = JSON.parse(request.responseText);
      console.debug(`data from getWikipediaSearchLink is ${request.responseText}`);
      // from the list of links get the first one
      // from the list of results select first one
      [queryTopResultLink, queryTopResultText] = [data[3][0], data[1][0]];

      // Create suggestion list
      const l = ['<ul class="suggestionsList list-group list-group-flush">'];

      for (let i = 0; i < 10; i += 1) {
        const textLink = data[3][i];
        const text = data[1][i];
        if (text) {
          const matchText = matchString(searchQueryText, text);
          const unmatchedText = text.slice(matchText.length, text.length);
          // console.debug(`${searchQueryText}-->`, matchText, '||', unmatchedText)
          if (matchText) {
            if (unmatchedText) {
              l.push(` <li class="sl${i} listitem" id="${textLink}"><span id="${textLink}" style="font-weight:600">${matchText}</span><span id="${textLink}">${unmatchedText}</span></li>`);
            } else {
              l.push(` <li class="sl${i} listitem" id="${textLink}"><b id="${textLink}">${matchText}</b></li>`);
            }
          }
          // document.querySelector('.suggestions').append(ii)
        }
      }

      searchSuggestionList.innerHTML = l.join('');
      l.push('</ul>');

      // If some item in the list is clicked then fetch data related to that item
      const suggestionList = document.querySelector('.suggestionsList');
      suggestionList.addEventListener('click', (e) => {
        console.debug(e.target.nodeName);
        if (e.target && (['LI', 'SPAN', 'B'].includes(e.target.nodeName))) {
          const wikiArticleLink = e.target.id;
          console.debug(`List item is ${wikiArticleLink}`);
          queryResultLink = String(wikiArticleLink);
          queryResultText = String(wikiArticleLink.split('/').slice(-1));
          searchQueryInsideInputBox('both', e.target.id);
        }
      });

      // If mouse over some list item then highlight that line
      for (let i = 0; i < 10; i += 1) {
        const suggestionListItem = document.querySelector(`.sl${i}`);
        suggestionListItem.addEventListener('mouseover', (e) => {
          if (e.target && (['LI', 'SPAN', 'B'].includes(e.target.nodeName))) {
            suggestionListItem.style.backgroundColor = '#eef3f5';
            suggestionListItem.style.borderRadius = 9;
          }
        });
        suggestionListItem.addEventListener('mouseout', (e) => {
          if (e.target && (['LI', 'SPAN', 'B'].includes(e.target.nodeName))) {
            suggestionListItem.style.backgroundColor = 'white';
          }
        });
      }
    };
    request.send(null);
  }


  // #############################################################################
  // ## Search query and suggestion List
  // #############################################################################



  function defaultStyle() {
    // console.debug(`searchBox.value is ${searchBox.value}`)
    if (!searchBox.value) {
      searchMainDiv.style.borderRadius = '24px';
      searchMainDiv.style.boxShadow = 'none';
      searchMainDiv.style.borderColor = 'rgb(223, 225, 229)';
      searchSuggestion.style.display = 'none';
    } else {
      searchMainDiv.style.borderRadius = '24px';
      searchMainDiv.style.boxShadow = '0 1px 6px 0 rgba(32,33,36,0.28)';
      searchMainDiv.style.borderColor = 'rgba(223,225,229,0)';
      searchSuggestion.style.display = 'none';
    }
  }

  function focusedStyle() {
    if (searchBox.value) {
      searchMainDiv.style.borderBottomRightRadius = 0;
      searchMainDiv.style.borderBottomLeftRadius = 0;
      searchMainDiv.style.boxShadow = '0 1px 6px 0 rgba(32,33,36,0.28)';
      searchMainDiv.style.borderColor = 'rgba(223,225,229,0)';
      searchSuggestion.style.display = 'flex';
    } else {
      searchMainDiv.style.borderRadius = '24px';
      searchMainDiv.style.boxShadow = '0 1px 6px 0 rgba(32,33,36,0.28)';
      searchMainDiv.style.borderColor = 'rgba(223,225,229,0)';
      searchSuggestion.style.display = 'none';
    }
  }

  function mouseoverMainDiv() {
    searchMainDiv.style.boxShadow = '0 1px 6px 0 rgba(32,33,36,0.28)';
    searchMainDiv.style.borderColor = 'rgba(223,225,229,0)';
  }

  function mouseoutMainDiv() {
    searchMainDiv.style.boxShadow = 'none';
    searchMainDiv.style.borderColor = 'rgb(223, 225, 229)';
  }

  function searchQueryInsideInputBox(actionType, query) {
    console.debug(`query for search is ${query}`);
    defaultStyle();
    const searchQuery = query.trim();
    if (searchQuery) {
      getAudioFileData(actionType, query);
    }
    // else {

    // }
  }

  function showSuggestionsForQueryInInputBox(query) {
    focusedStyle();
    const searchQuery = query.trim();
    console.debug(`search query for showing suggestions is ${searchQuery}`);
    if (searchQuery) {
      getWikipediaresponseAsList(searchQuery);
    }
  }

  searchIcon.addEventListener('click', () => {
    queryResultText = String(queryTopResultText);
    queryResultLink = String(queryTopResultLink);
    searchQueryInsideInputBox('both', queryTopResultLink);
  });

  mainDiv.addEventListener('mouseover', () => {
    mouseoverMainDiv();
  });

  mainDiv.addEventListener('mouseout', () => {
    if (searchBox.value === '') {
      mouseoutMainDiv();
    } else {
      mouseoverMainDiv();
    }
  });

  searchBox.addEventListener('keyup', (e) => {
    console.debug(`keyup event happended ${e.target.value}`);
    const query = e.target.value;
    if (e.key === 'Enter' && query) {
      if (!queryTopResultLink) {
        getWikipediaresponseAsList(query);
      }
      queryResultText = String(queryTopResultText);
      queryResultLink = String(queryTopResultLink);
      searchQueryInsideInputBox('both', queryTopResultLink);
    }
  });

  searchBox.addEventListener('input', (e) => {
    console.debug(`input event ${e.data}`);
    console.debug(`input event with target value ${e.target.value}`);
    showSuggestionsForQueryInInputBox(e.target.value);
  });

  languageSelector.addEventListener('click', () => {
    const query = searchBox.value;
    queryLanguage = languageSelector.options[languageSelector.selectedIndex].value;
    console.log(`Selected language is ${queryLanguage}`);
    showSuggestionsForQueryInInputBox(query);
  });

  document.addEventListener('click', (e) => {
    const { target } = e;
    const clickVal = mainDiv.contains(target);
    if (target.className === 'accordianCardLinks') {
      const wikipediaArticleLink = target.id;
      console.debug(wikipediaArticleLink);
      getAudioFileData('showAudioModal', wikipediaArticleLink);
    } else if (clickVal) {
      focusedStyle();
    } else {
      defaultStyle();
    }
  });
});

// ==UserScript==
// @name        부동산 매물 가격 필터 for 월부_Upgrade / addClickFnc / shinhoLightFnc + JSON Export
// @namespace   Violentmonkey Scripts
// @match       https://new.land.naver.com/complexes*
// @version     2.0
// @author      모느나 + Python Integration
// @description Naver Real Estate Full Features + JSON Export
// @require     https://code.jquery.com/jquery-1.12.4.min.js
// @require     https://cdnjs.cloudflare.com/ajax/libs/clipboard.js/2.0.10/clipboard.min.js
// ==/UserScript==


new ClipboardJS('.copyBtn');

let isCreateCheckArea = false
let checkAreaValue = false

const AREA_CHECK = 'area_check';
const LOW_JEONSE_CHECK = 'low_jeonse_check'
const SEANGO_CHECK = 'seango_check'
const SHINHO_RADIO = 'shiho_radio'

const STORE_NAME = 'wolbu_price_filter'
const STORE_VALUE = { [AREA_CHECK]: false, [LOW_JEONSE_CHECK]: false, [SEANGO_CHECK]: false };

const SIGN_LOW_VALUE = 5;
const SIGN_MIDDLE_VALUE = 10;

const validityCheck = {
    [SHINHO_RADIO]: { isCreate: false, value: 1, defValue: [{ val: 1, text: "X1" }, { val: 2, text: "X2" }, { val: 3, text: "X3" }], title: "신호등", type: "radio" }
    , [SEANGO_CHECK]: { isCreate: false, value: false, title: "세안고포함", type: "check" }
    , [LOW_JEONSE_CHECK]: { isCreate: false, value: false, title: "최저전세값", type: "check" }
    , [AREA_CHECK]: { isCreate: false, value: false, title: "35평이상 포함", type: "check" }
}


// get local store value
function getStoreValue(id) {

    let storeVal = localStorage.getItem(STORE_NAME);

    if (!storeVal) {
        localStorage.setItem(STORE_NAME, JSON.stringify(STORE_VALUE));
        storeVal = localStorage.getItem(STORE_NAME);
    }


    return JSON.parse(storeVal)[id]

}

// set local store value
function setStoreValue(id, val) {

    let storeVal = localStorage.getItem(STORE_NAME)

    if (!storeVal)
        localStorage.setItem(STORE_NAME, JSON.stringify(STORE_VALUE));

    let parseVal = JSON.parse(storeVal);
    parseVal[id] = val;
    localStorage.setItem(STORE_NAME, JSON.stringify(parseVal));

}

function CheckBox(id, target) {

    this.div_id = 'div_' + id;
    this.id = id;
    this.labelText = validityCheck[id].title;
    this.divEle = this.init();
    target.after(this.divEle);

    let storeVal = getStoreValue(this.id);
    validityCheck[id].value = storeVal
    document.querySelector('#' + id).checked = storeVal;

    document.querySelector('#' + id).addEventListener('change', function (e) {
        validityCheck[id].value = this.checked;
        setStoreValue(id, this.checked)

    });
    validityCheck[id].isCreate = true;

}

CheckBox.prototype = {
    constructor: CheckBox
    , init: function () {

        const divEle = document.createElement('div');
        divEle.setAttribute('id', this.div_id)
        divEle.classList.add('filter_group', 'filter_group--size');
        divEle.style.margin = '6px 10px 0 0';
        divEle.innerHTML = '<input type="checkbox" name="type" id="' + this.id + '" class="checkbox_input" ><label for="' + this.id + '" class="checkbox_label">' + this.labelText + '</label>';
        return divEle;

    }
}



function RadioBox(id, target) {

    this.div_id = 'div_' + id;
    this.id = id;
    this.valArr = validityCheck[id].defValue;
    this.divEle = this.init();
    target.after(this.divEle);

    let storeVal = getStoreValue(this.id) || 1;
    validityCheck[id].value = storeVal;

    $("input:radio[name=signal]:radio[value='" + storeVal + "']").prop("checked", true);

    $('input[type=radio][name=signal]').change(function () {
        console.log($(this).val())
        validityCheck[id].value = $(this).val();
        setStoreValue(id, $(this).val())
    });

    validityCheck[id].isCreate = true;

}

RadioBox.prototype = {
    constructor: RadioBox
    , init: function () {

        const divEle = document.createElement('div');
        divEle.setAttribute('id', this.div_id)
        divEle.classList.add('filter_group', 'filter_group--size');
        divEle.style.margin = '6px 10px 0 0';

        let radioBoxs = "";
        for (let i = 0; i < this.valArr.length; i++) {

            let val = this.valArr[i];
            radioBoxs += `<input type="radio" name="signal" id="shinho_${i}" class="radio_input" value="${val.val}"><label for="shinho_${i}" class="radio_label" style="margin-right: 10px; padding-left: 20px;">${val.text}</label>`;
        }


        divEle.innerHTML = radioBoxs;
        return divEle;

    }
}

// 신호등 불빛 결정
function sinhoCheck(signalVal, gap) {
    console.log('signalVal', signalVal)
    let multiple = validityCheck[SHINHO_RADIO].value;
    let tootip = `${signalVal}% / ${gap}`

    if (signalVal < (SIGN_LOW_VALUE * multiple)) return ['green', tootip];
    else if (signalVal <= (SIGN_MIDDLE_VALUE * multiple)) return ['orange', tootip];
    return ['red', tootip]

}

function createBox(key, type) {
    if (type === "check")
        new CheckBox(key, document.querySelector('.filter_btn_detail'));
    else
        new RadioBox(key, document.querySelector('.filter_btn_detail'));
}

function checkMandantoryCondition(size) {
    if (validityCheck[AREA_CHECK].value) return true;

    // 35평 미만
    if (/\d+/g.exec(size) > (35 * 3.3)) {
        return false;
    }
    return true;
}

function getFloor(strFloor) {
    return strFloor.replace("층", "").split('/');
}

function checkItemCondition(tradeType, floor, spec) {

    //매매, 전세
    if (tradeType != "전세" && tradeType != "매매") {
        return false;
    }

    // 세안고 제외
    if (!validityCheck[SEANGO_CHECK].value && (spec.includes("끼고") || spec.includes("안고") || spec.includes("승계"))) {
        return false;
    }

    // 층 - 전세의 경우 층에 관계없이 최고가 적용
    if (tradeType == "매매") {
        var _floorInfo = getFloor(floor);
        if (_floorInfo[0] == "저") {
            return false;
        }
        // 1층, 2층, 탑층 제외
        if ("1|2|3".indexOf(_floorInfo[0]) > -1 || _floorInfo[0] == _floorInfo[1]) {
            return false;
        }

        // 5층 이상 건물에서 3층 이하 제외
        if (_floorInfo[1] >= 5 && _floorInfo[0] <= 3) {
            return false;
        }
    }
    return true;
}

function parsePrice(tradePrice) {
    tradePrice = tradePrice.replace(" ", "").replace(",", "");
    if (tradePrice.includes("억"))
        return parseInt(tradePrice.split("억")[0] * 10000) + (parseInt(tradePrice.split("억")[1]) || 0);
    else
        return parseInt(tradePrice)
}

function getPrice_WeolbuStandard() {

    let result = {};
    let dictPricePerSize = {};
    let tradeTypeValueFnc = function (tradeType, befVal, newVal) {

        let price, floor, spec;

        if (tradeType === '매매') {
            price = befVal[0] > newVal[0] ? newVal[0] : befVal[0]
            floor = befVal[0] > newVal[0] ? newVal[1] : befVal[1]
        } else {

            if (validityCheck[LOW_JEONSE_CHECK].value)
                price = befVal[0] < newVal[0] ? befVal[0] : newVal[0]
            else
                price = befVal[0] < newVal[0] ? newVal[0] : befVal[0]

            floor = befVal[0] < newVal[0] ? newVal[1] : befVal[1]

        }

        return [price, floor, befVal[2] + newVal[2], ++befVal[3]];

    }



    document.querySelectorAll("#articleListArea > div").forEach(function (ele) {
        let aptInfo = ele.querySelectorAll("div.info_area .line .spec")[0].innerText.split(", ");
        let size = aptInfo[0];
        let floor = aptInfo[1];
        let tradeType = ele.querySelector("div.price_line .type").innerText;
        let tradePrice = parsePrice(ele.querySelector("div.price_line .price").innerText);
        let spec = ele.querySelectorAll(" div.info_area > p:nth-child(2) > span")[0];
        spec = spec ? spec.innerText : "";



        if ("매매|전세".indexOf(tradeType) > -1) {
            if (!checkMandantoryCondition(size)) {
                return;
            }

            if (!(size in result)) {
                result[size] = { '매매': 0, '전세': 0, '갭': 0, '전세가율': '-', '매매층': '-', '전세층': '-', '매매갯수': 0, '전세갯수': '0', '매매신': '' };
                dictPricePerSize[size] = { "매매": {}, "전세": {} };
            }

            if (!document.querySelector('#address_group2').checked) {
                if (!dictPricePerSize[size][tradeType][aptInfo.join(',')]) {
                    dictPricePerSize[size][tradeType][aptInfo.join(',')] = [tradePrice, getFloor(floor)[0], spec, 1]
                }
                else {
                    let beforeValue = dictPricePerSize[size][tradeType][aptInfo.join(',')];
                    let newValue = [tradePrice, getFloor(floor)[0], spec];

                    dictPricePerSize[size][tradeType][aptInfo.join(',')] = tradeTypeValueFnc(tradeType, beforeValue, newValue)

                }
            }
            else {
                if (!dictPricePerSize[size][tradeType][aptInfo.join(',') + "_" + tradePrice]) {
                    dictPricePerSize[size][tradeType][aptInfo.join(',') + "_" + tradePrice] = [tradePrice, getFloor(floor)[0], spec, 1]
                }
                else {
                    let beforeValue = dictPricePerSize[size][tradeType][aptInfo.join(',') + "_" + tradePrice];
                    let newValue = [tradePrice, getFloor(floor)[0], spec];

                    dictPricePerSize[size][tradeType][aptInfo.join(',') + "_" + tradePrice] = tradeTypeValueFnc(tradeType, beforeValue, newValue)

                }
            }

        }

    });


    let isGrouped = document.querySelector('#address_group2').checked;

    for (let key in result) {
        let sellObj = dictPricePerSize[key]['매매'];
        let liveObj = dictPricePerSize[key]['전세'];

        let sellCnt = !isGrouped ? Object.keys(sellObj).length : Object.entries(sellObj).reduce((acc, [, item]) => (parseInt(acc) + parseInt(item[3])), 0);
        let liveCnt = !isGrouped ? Object.keys(liveObj).length : Object.entries(liveObj).reduce((acc, [, item]) => (parseInt(acc) + parseInt(item[3])), 0);

        for (let key in sellObj) {

            let aptObj = sellObj[key];

            if (!checkItemCondition('매매', key.split(",")[1], aptObj[2])) {

                delete sellObj[key]
            }
        }

        let finalSellObj = Object.entries(sellObj).sort(([, a], [, b]) => a[0] - b[0]);
        let finalLivelObj = Object.entries(liveObj).sort(([, a], [, b]) => b[0] - a[0]);

        if (finalSellObj && finalSellObj.length) {
            let sellPrice = finalSellObj[0][1][0];

            result[key]['매매'] = finalSellObj[0][1][0];
            result[key]['매매층'] = finalSellObj[0][1][1];


            // 신호등 기능
            if (isGrouped) {
                let compareObj = finalSellObj.filter(item => item[1][0] > sellPrice);

                if (compareObj && compareObj.length) {

                    let comparePrice = compareObj[0][1][0];
                    let compareRate = (100 - (parseInt(sellPrice) / comparePrice * 100)).toFixed(1);

                    console.log('비교값', result[key], comparePrice);
                    result[key]['매매신'] = sinhoCheck(compareRate, comparePrice - parseInt(sellPrice))
                }
            }


        }

        result[key]['매매갯수'] = sellCnt;

        if (finalLivelObj && finalLivelObj.length) {
            let idx = validityCheck[LOW_JEONSE_CHECK].value ? finalLivelObj.length - 1 : 0;

            result[key]['전세'] = finalLivelObj[idx][1][0];
            result[key]['전세층'] = finalLivelObj[idx][1][1];
            result[key]['전세갯수'] = liveCnt;

            result[key]['갭'] = parseInt(result[key]['매매']) - parseInt(result[key]['전세']);
            result[key]['전세가율'] = parseInt(parseInt(result[key]['전세']) / parseInt(result[key]['매매']) * 100) + "%";
        }
    }

    return result;
}

// 신호등 그리기
function makeShinhoDot(shinhoColor) {

    let canvasDiv = document.createElement("div");
    canvasDiv.style.display = "inline"

    if (typeof shinhoColor === 'object') {
        canvasDiv.title = shinhoColor[1]
        shinhoColor = shinhoColor[0]
    }


    let canvas = document.createElement('canvas')
    canvas.width = 20
    canvas.height = 20
    const ctx = canvas.getContext("2d");
    ctx.beginPath();
    ctx.arc(8, 8, 4, 0, 2 * Math.PI);
    ctx.stroke();
    ctx.fillStyle = shinhoColor;
    ctx.fill();
    canvasDiv.appendChild(canvas);
    return canvasDiv;

}


function addInfoToScreen(infos) {

    let isGrouped = document.querySelector('#address_group2').checked;
    var oldScreenInfo = document.querySelector("#summaryInfo > div.complex_summary_info > div.complex_price_info");
    if (oldScreenInfo)
        oldScreenInfo.remove();

    var screenInfo = document.createElement('div');
    screenInfo.setAttribute('class', 'complex_price_info');
    screenInfo.style.marginTop = "10px";

    let isFirst = true;

    for (let size in infos) {

        var strTradePriceInfo = (infos[size]['매매'] ? infos[size]['매매'] + "/" + infos[size]['매매층'] : "0/-");
        var strLeasePriceInfo = (infos[size]['전세'] ? infos[size]['전세'] + "/" + infos[size]['전세층'] : "0/-");

        var additionalInfos = [];
        if (infos[size]['매매'] && infos[size]['전세']) {
            additionalInfos.push(infos[size]['갭']);
            additionalInfos.push(infos[size]['전세가율']);
        }

        if (infos[size]['매매']) {
            var py = parseInt(/\d+/g.exec(size), 10) / 3.3;
            additionalInfos.push(parseInt(infos[size]['매매'] / py) + "/3.3m²");
        }

        var strAdditionalInfo = "";

        if (document.querySelector('#address_group2').checked)
            strAdditionalInfo += additionalInfos.length > 0 ? "  (" + additionalInfos.join(", ") + ")(" + infos[size]['매매갯수'] + "/" + infos[size]['전세갯수'] + ")" : "  (" + infos[size]['매매갯수'] + "/" + infos[size]['전세갯수'] + ")";
        else
            strAdditionalInfo += additionalInfos.length > 0 ? "  (" + additionalInfos.join(", ") + ")" : "";


        //신호등 description
        if (isGrouped && isFirst) {

            let multiple = validityCheck[SHINHO_RADIO].value;

            let shinhoDesc = document.querySelector("#summaryInfo > div.complex_summary_info > div.complex_trade_wrap > div > dl:nth-child(1)").cloneNode();
            shinhoDesc.setAttribute("added", true);
            let shinhoDt = document.createElement("dt")
            let greenDot = makeShinhoDot('green')
            let orangeDot = makeShinhoDot('orange')
            let redDot = makeShinhoDot('red')


            let greenDescEle = document.createElement("span")
            greenDescEle.innerHTML = `${SIGN_LOW_VALUE * multiple}%미만`;
            greenDescEle.style.margin = "0 8px 0 -3px";
            greenDescEle.classList.add('data');

            let orangeDescEle = document.createElement("span")
            orangeDescEle.innerHTML = `${SIGN_MIDDLE_VALUE * multiple}%미만`;
            orangeDescEle.style.margin = "0 8px 0 -3px";
            orangeDescEle.classList.add('data');

            let redDescEle = document.createElement("span")
            redDescEle.innerHTML = `${SIGN_MIDDLE_VALUE * multiple}%이상`;
            redDescEle.style.margin = "0 8px 0 -3px";
            redDescEle.classList.add('data');


            shinhoDt.appendChild(greenDot);
            shinhoDt.appendChild(greenDescEle);

            shinhoDt.appendChild(orangeDot);
            shinhoDt.appendChild(orangeDescEle);

            shinhoDt.appendChild(redDot);
            shinhoDt.appendChild(redDescEle);

            shinhoDesc.style.lineHeight = '1px';
            shinhoDesc.appendChild(shinhoDt);
            screenInfo.appendChild(shinhoDesc);
            isFirst = false;

        }


        var cloned = document.querySelector("#summaryInfo > div.complex_summary_info > div.complex_trade_wrap > div > dl:nth-child(1)").cloneNode(true);
        cloned.setAttribute("added", true);
        cloned.getElementsByClassName("title")[0].innerHTML = `<button class="copyBtn" data-clipboard-text="${strTradePriceInfo}/${strLeasePriceInfo}" onMouseOver="this.style.color='red'" onMouseOut="this.style.color='#555'" onMouseDown="this.style.color='#1F75FE'" onMouseUp="this.style.color='red'">${size}</button>`;

        var trade = cloned.getElementsByClassName("data")[0];
        var lease = trade.cloneNode(true);
        var additionalInfo = trade.cloneNode(true);
        var delim = trade.cloneNode(true);

        trade.innerText = strTradePriceInfo;
        trade.style.color = '#f34c59';
        lease.innerText = strLeasePriceInfo;
        lease.style.color = '#4c94e8';
        delim.innerText = " / ";
        delim.style.color = '#ffffff';
        additionalInfo.innerText = strAdditionalInfo;

        cloned.removeChild(trade);

        cloned.appendChild(delim);
        cloned.appendChild(trade);
        cloned.appendChild(delim.cloneNode(true));
        cloned.appendChild(lease);
        cloned.appendChild(delim.cloneNode(true));
        cloned.appendChild(additionalInfo);

        if (isGrouped && infos[size]['매매'] !== 0 && infos[size]['매매신'] !== '')
            cloned.appendChild(makeShinhoDot(infos[size]['매매신']));

        cloned.style.lineHeight = '1px';
        screenInfo.appendChild(cloned);
    }

    document.querySelector("#summaryInfo > div.complex_summary_info").insertBefore(screenInfo, document.querySelector("#summaryInfo > div.complex_summary_info > div.complex_detail_link"))
}




function sortOnKeys(dict) {

    var tempDict = {};

    let sorted = jQuery('#complexOverviewList > div.list_contents > div.list_fixed > div.list_filter > div > div:nth-child(2) > div > div > ul > li label.checkbox_label')
        .map((idx, item) => {
            return item.innerText.replace('㎡', '');
        })


    let keys = Object.keys(dict)


    sorted.map((idx, item) => {
        keys.map((key) => {
            if (key.indexOf(item) === 0) tempDict[key] = dict[key]
        })
    })

    return tempDict;
}


var g_lastSelectedApt = "";

function addObserverIfDesiredNodeAvailable() {
    var target = document.getElementsByClassName('map_wrap')[0];
    var inDebounce;
    if (!target)
        return;

    for (let key in validityCheck) {
        let obj = validityCheck[key]

        if (!obj.isCreate)
            createBox(key, obj.type)
    }

    jQuery(document).on('click', (e) => {

        if (jQuery(e.target).parents('a.item_link').length > 0 || e.target.className === 'complex_link')
            setTimeout((runFnc) => { jQuery('.detail_panel').css("left", "450px"); }, 500);

    });



    var observer = new MutationObserver(function (mutations) {

        mutations.forEach(function (mutation) {
            [].slice.call(mutation.addedNodes).forEach(function (addedNode) {

                if (!addedNode.classList ||
                    (!addedNode.classList.contains('infinite_scroll') && !addedNode.classList.contains('item'))) {
                    return;
                }

                if (!document.querySelector("#complexTitle")) {
                    console.log("Unexpected issues #1");
                    return;
                }

                if (document.querySelector("#complexTitle").innerText != g_lastSelectedApt) {
                    document.querySelectorAll("#summaryInfo > div.complex_summary_info > div.complex_trade_wrap > div > dl").forEach(function (ele) {
                        if (ele.hasAttribute("added"))
                            ele.remove();
                    });
                    g_lastSelectedApt = document.querySelector("#complexTitle").innerText;
                }

                document.querySelector("#complexOverviewList > div > div.item_area > div").scrollTop =
                    document.querySelector("#complexOverviewList > div > div.item_area > div").scrollHeight;

                var runFnc = function () {

                    jQuery('.list_panel').css("width", "450px");
                    jQuery('.detail_panel').css("left", "450px");
                    result = getPrice_WeolbuStandard();
                    result = sortOnKeys(result);
                    addInfoToScreen(result);
                    document.querySelector(".item_list--article").scrollTop = 0;
                }

                if (inDebounce) clearTimeout(inDebounce)
                inDebounce = setTimeout(runFnc, 500);


            });
        });
    });

    var config = {
        childList: true,
        subtree: true,
    };

    observer.observe(target, config);

}

addObserverIfDesiredNodeAvailable();

// ========================================
// JSON 내보내기 기능 추가
// ========================================

function exportComplexToJSON() {
    console.log('JSON 내보내기 시작...');

    const complexName = document.querySelector("#complexTitle") ?
        document.querySelector("#complexTitle").innerText : "Unknown";

    const urlPath = window.location.pathname;
    const complexNo = urlPath.split('/complexes/')[1]?.split('?')[0] || 'unknown';

    const address = document.querySelector("#complexTitle ~ .text") ?
        document.querySelector("#complexTitle ~ .text").innerText : "";

    // 세대수 추출
    let totalHouseholds = 0;
    const summaryText = document.querySelector("#summaryInfo")?.innerText || "";
    const householdsMatch = summaryText.match(/(\d+(?:,\d+)*)\s*세대/);
    if (householdsMatch) {
        totalHouseholds = parseInt(householdsMatch[1].replace(/,/g, ''));
    }

    const priceData = getPrice_WeolbuStandard();

    const exportData = {
        metadata: {
            complex_no: complexNo,
            complex_name: complexName,
            address: address,
            total_households: totalHouseholds,
            collected_at: new Date().toISOString(),
            collector: 'tampermonkey_script'
        },
        listings: []
    };

    for (let areaType in priceData) {
        const item = priceData[areaType];

        if (item['매매'] || item['전세']) {
            const areaMatch = areaType.match(/(\d+\.?\d*)m/);
            const exclusiveArea = areaMatch ? parseFloat(areaMatch[1]) : 0;

            const listing = {
                area_type: areaType,
                exclusive_area: exclusiveArea,
                sale_price: item['매매'] || 0,
                sale_floor: item['매매층'] || '',
                sale_count: item['매매갯수'] || 0,
                lease_price: item['전세'] || 0,
                lease_floor: item['전세층'] || '',
                lease_count: item['전세갯수'] || 0,
                gap: item['갭'] || 0,
                lease_rate: item['전세가율'] || ''
            };

            exportData.listings.push(listing);
        }
    }

    const jsonString = JSON.stringify(exportData, null, 2);
    const blob = new Blob([jsonString], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `naver_${complexName.replace(/\s+/g, '_')}_${Date.now()}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);

    console.log('JSON 내보내기 완료!', exportData);
    alert(`✓ ${complexName} 데이터 내보내기 완료!\n면적 타입: ${exportData.listings.length}개`);
}

function addExportButton() {
    const existingBtn = document.getElementById('json-export-btn');
    if (existingBtn) existingBtn.remove();

    const exportBtn = document.createElement('button');
    exportBtn.id = 'json-export-btn';
    exportBtn.innerHTML = '📥 Python으로 내보내기';
    exportBtn.onclick = exportComplexToJSON;

    exportBtn.style.cssText = `
        position: fixed;
        top: 70px;
        right: 10px;
        z-index: 9999;
        padding: 12px 20px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 8px;
        font-size: 14px;
        font-weight: bold;
        cursor: pointer;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        transition: all 0.3s ease;
    `;

    exportBtn.onmouseover = function () {
        this.style.transform = 'translateY(-2px)';
        this.style.boxShadow = '0 6px 20px rgba(0,0,0,0.3)';
    };
    exportBtn.onmouseout = function () {
        this.style.transform = 'translateY(0)';
        this.style.boxShadow = '0 4px 15px rgba(0,0,0,0.2)';
    };

    document.body.appendChild(exportBtn);
}

setTimeout(addExportButton, 2000);

const exportObserver = new MutationObserver(function (mutations) {
    mutations.forEach(function (mutation) {
        if (mutation.addedNodes.length > 0) {
            const complexTitle = document.querySelector("#complexTitle");
            if (complexTitle && !document.getElementById('json-export-btn')) {
                setTimeout(addExportButton, 500);
            }
        }
    });
});

if (document.querySelector('.map_wrap')) {
    exportObserver.observe(document.querySelector('.map_wrap'), {
        childList: true,
        subtree: true
    });
}

console.log('✓ 모든 기능이 포함된 Tampermonkey 스크립트 로드 완료');

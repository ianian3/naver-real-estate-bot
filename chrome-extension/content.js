// Chrome Extension Content Script
// 네이버 부동산 분석 도우미 v1.0.0

(function () {
    'use strict';

    // jQuery noConflict 모드
    const $ = jQuery.noConflict(true);

    console.log('✓ 네이버 부동산 분석 도우미 로드 시작...');

    // ClipboardJS 초기화 (DOM 준비 후)
    let clipboard = null;
    function initClipboard() {
        if (typeof ClipboardJS !== 'undefined') {
            clipboard = new ClipboardJS('.copyBtn');
            console.log('✓ ClipboardJS 초기화 완료');
        }
    }

    let isCreateCheckArea = false;
    let checkAreaValue = false;

    const AREA_CHECK = 'area_check';
    const LOW_JEONSE_CHECK = 'low_jeonse_check';
    const SEANGO_CHECK = 'seango_check';
    const SHINHO_RADIO = 'shiho_radio';

    const STORE_NAME = 'wolbu_price_filter';
    const STORE_VALUE = { [AREA_CHECK]: false, [LOW_JEONSE_CHECK]: false, [SEANGO_CHECK]: false };

    const SIGN_LOW_VALUE = 5;
    const SIGN_MIDDLE_VALUE = 10;

    const validityCheck = {
        [SHINHO_RADIO]: { isCreate: false, value: 1, defValue: [{ val: 1, text: "X1" }, { val: 2, text: "X2" }, { val: 3, text: "X3" }], title: "신호등", type: "radio" },
        [SEANGO_CHECK]: { isCreate: false, value: false, title: "세안고포함", type: "check" },
        [LOW_JEONSE_CHECK]: { isCreate: false, value: false, title: "최저전세값", type: "check" },
        [AREA_CHECK]: { isCreate: false, value: false, title: "35평이상 포함", type: "check" }
    };

    function getStoreValue(id) {
        let storeVal = localStorage.getItem(STORE_NAME);
        if (!storeVal) {
            localStorage.setItem(STORE_NAME, JSON.stringify(STORE_VALUE));
            storeVal = localStorage.getItem(STORE_NAME);
        }
        return JSON.parse(storeVal)[id];
    }

    function setStoreValue(id, val) {
        let storeVal = localStorage.getItem(STORE_NAME);
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
        validityCheck[id].value = storeVal;
        document.querySelector('#' + id).checked = storeVal;

        document.querySelector('#' + id).addEventListener('change', function (e) {
            validityCheck[id].value = this.checked;
            setStoreValue(id, this.checked);
        });
        validityCheck[id].isCreate = true;
    }

    CheckBox.prototype = {
        constructor: CheckBox,
        init: function () {
            const divEle = document.createElement('div');
            divEle.setAttribute('id', this.div_id);
            divEle.classList.add('filter_group', 'filter_group--size');
            divEle.style.margin = '6px 10px 0 0';
            divEle.innerHTML = '<input type="checkbox" name="type" id="' + this.id + '" class="checkbox_input" ><label for="' + this.id + '" class="checkbox_label">' + this.labelText + '</label>';
            return divEle;
        }
    };

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
            validityCheck[id].value = $(this).val();
            setStoreValue(id, $(this).val());
        });
        validityCheck[id].isCreate = true;
    }

    RadioBox.prototype = {
        constructor: RadioBox,
        init: function () {
            const divEle = document.createElement('div');
            divEle.setAttribute('id', this.div_id);
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
    };

    function sinhoCheck(signalVal, gap) {
        let multiple = validityCheck[SHINHO_RADIO].value;
        let tootip = `${signalVal}% / ${gap}`;
        if (signalVal < (SIGN_LOW_VALUE * multiple)) return ['green', tootip];
        else if (signalVal <= (SIGN_MIDDLE_VALUE * multiple)) return ['orange', tootip];
        return ['red', tootip];
    }

    function createBox(key, type) {
        if (type === "check")
            new CheckBox(key, document.querySelector('.filter_btn_detail'));
        else
            new RadioBox(key, document.querySelector('.filter_btn_detail'));
    }

    function checkMandantoryCondition(size) {
        if (validityCheck[AREA_CHECK].value) return true;
        if (/\d+/g.exec(size) > (35 * 3.3)) {
            return false;
        }
        return true;
    }

    function getFloor(strFloor) {
        return strFloor.replace("층", "").split('/');
    }

    function checkItemCondition(tradeType, floor, spec) {
        if (tradeType != "전세" && tradeType != "매매") {
            return false;
        }
        if (!validityCheck[SEANGO_CHECK].value && (spec.includes("끼고") || spec.includes("안고") || spec.includes("승계"))) {
            return false;
        }
        if (tradeType == "매매") {
            var _floorInfo = getFloor(floor);
            if (_floorInfo[0] == "저") {
                return false;
            }
            if ("1|2|3".indexOf(_floorInfo[0]) > -1 || _floorInfo[0] == _floorInfo[1]) {
                return false;
            }
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
            return parseInt(tradePrice);
    }

    function extractAreaFromKey(areaKey) {
        const match = areaKey.match(/(\d+)m/);
        return match ? parseInt(match[1]) : 0;
    }

    function getPrice_WeolbuStandard() {
        let result = {};
        let dictPricePerSize = {};
        let tradeTypeValueFnc = function (tradeType, befVal, newVal) {
            let price, floor;
            if (tradeType === '매매') {
                price = befVal[0] > newVal[0] ? newVal[0] : befVal[0];
                floor = befVal[0] > newVal[0] ? newVal[1] : befVal[1];
            } else {
                if (validityCheck[LOW_JEONSE_CHECK].value)
                    price = befVal[0] < newVal[0] ? befVal[0] : newVal[0];
                else
                    price = befVal[0] < newVal[0] ? newVal[0] : befVal[0];
                floor = befVal[0] < newVal[0] ? newVal[1] : befVal[1];
            }
            return [price, floor, befVal[2] + newVal[2], ++befVal[3]];
        };

        const articleListArea = document.querySelector("#articleListArea");
        if (!articleListArea) {
            console.log('⚠️ articleListArea를 찾을 수 없습니다');
            return result;
        }

        // .item 클래스를 가진 매물 아이템 찾기
        const articles = articleListArea.querySelectorAll(".item");
        console.log(`📍 찾은 매물: ${articles.length}개`);

        if (articles.length === 0) {
            console.log('⚠️ 매물 아이템을 찾을 수 없습니다');
            return result;
        }

        articles.forEach(function (ele, idx) {
            try {
                // 여러 가능한 spec 선택자 시도
                let specElement = ele.querySelector(".spec") ||
                    ele.querySelector("div.info_area .line .spec") ||
                    ele.querySelector(".item_inner .spec");
                if (!specElement) return;

                // spec 텍스트에서 면적, 층수 파싱 (예: "108/84m², 저/18층, 남동향")
                let specText = specElement.innerText;
                let aptInfo = specText.split(", ");
                let size = aptInfo[0] || "";
                let floor = aptInfo[1] || "";

                // type과 price 선택자 (여러 패턴 시도)
                const typeElement = ele.querySelector(".type") ||
                    ele.querySelector("div.price_line .type") ||
                    ele.querySelector(".item_inner .type");
                const priceElement = ele.querySelector(".price") ||
                    ele.querySelector("div.price_line .price") ||
                    ele.querySelector(".item_inner .price");

                if (!typeElement || !priceElement) return;

                let tradeType = typeElement.innerText;
                let tradePrice = parsePrice(priceElement.innerText);

                // 추가 spec 정보 (세안고 등)
                let specSpans = ele.querySelectorAll(".text, div.info_area > p:nth-child(2) > span");
                let spec = specSpans.length > 0 ? specSpans[0].innerText : "";

                if ("매매|전세".indexOf(tradeType) > -1) {
                    if (!checkMandantoryCondition(size)) return;

                    if (!(size in result)) {
                        result[size] = { '매매': 0, '전세': 0, '갭': 0, '전세가율': '-', '매매층': '-', '전세층': '-', '매매갯수': 0, '전세갯수': '0', '매매신': '' };
                        dictPricePerSize[size] = { "매매": {}, "전세": {} };
                    }

                    const groupCheckbox = document.querySelector('#address_group2');
                    const isGrouped = groupCheckbox ? groupCheckbox.checked : false;

                    if (!isGrouped) {
                        if (!dictPricePerSize[size][tradeType][aptInfo.join(',')]) {
                            dictPricePerSize[size][tradeType][aptInfo.join(',')] = [tradePrice, getFloor(floor)[0], spec, 1];
                        } else {
                            let beforeValue = dictPricePerSize[size][tradeType][aptInfo.join(',')];
                            let newValue = [tradePrice, getFloor(floor)[0], spec];
                            dictPricePerSize[size][tradeType][aptInfo.join(',')] = tradeTypeValueFnc(tradeType, beforeValue, newValue);
                        }
                    } else {
                        if (!dictPricePerSize[size][tradeType][aptInfo.join(',') + "_" + tradePrice]) {
                            dictPricePerSize[size][tradeType][aptInfo.join(',') + "_" + tradePrice] = [tradePrice, getFloor(floor)[0], spec, 1];
                        } else {
                            let beforeValue = dictPricePerSize[size][tradeType][aptInfo.join(',') + "_" + tradePrice];
                            let newValue = [tradePrice, getFloor(floor)[0], spec];
                            dictPricePerSize[size][tradeType][aptInfo.join(',') + "_" + tradePrice] = tradeTypeValueFnc(tradeType, beforeValue, newValue);
                        }
                    }
                }
            } catch (e) {
                console.log(`[${idx}] 처리 오류:`, e.message);
            }
        });

        const groupCheckbox = document.querySelector('#address_group2');
        let isGrouped = groupCheckbox ? groupCheckbox.checked : false;

        for (let key in result) {
            let sellObj = dictPricePerSize[key]['매매'];
            let liveObj = dictPricePerSize[key]['전세'];

            let sellCnt = !isGrouped ? Object.keys(sellObj).length : Object.entries(sellObj).reduce((acc, [, item]) => (parseInt(acc) + parseInt(item[3])), 0);
            let liveCnt = !isGrouped ? Object.keys(liveObj).length : Object.entries(liveObj).reduce((acc, [, item]) => (parseInt(acc) + parseInt(item[3])), 0);

            for (let k in sellObj) {
                let aptObj = sellObj[k];
                if (!checkItemCondition('매매', k.split(",")[1], aptObj[2])) {
                    delete sellObj[k];
                }
            }

            let finalSellObj = Object.entries(sellObj).sort(([, a], [, b]) => a[0] - b[0]);
            let finalLivelObj = Object.entries(liveObj).sort(([, a], [, b]) => b[0] - a[0]);

            if (finalSellObj && finalSellObj.length) {
                let sellPrice = finalSellObj[0][1][0];
                result[key]['매매'] = finalSellObj[0][1][0];
                result[key]['매매층'] = finalSellObj[0][1][1];

                if (isGrouped) {
                    let compareObj = finalSellObj.filter(item => item[1][0] > sellPrice);
                    if (compareObj && compareObj.length) {
                        let comparePrice = compareObj[0][1][0];
                        let compareRate = (100 - (parseInt(sellPrice) / comparePrice * 100)).toFixed(1);
                        result[key]['매매신'] = sinhoCheck(compareRate, comparePrice - parseInt(sellPrice));
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

        console.log('✓ 최종 수집 결과:', result);
        return result;
    }

    function makeShinhoDot(shinhoColor) {
        let canvasDiv = document.createElement("div");
        canvasDiv.style.display = "inline";

        if (typeof shinhoColor === 'object') {
            canvasDiv.title = shinhoColor[1];
            shinhoColor = shinhoColor[0];
        }

        let canvas = document.createElement('canvas');
        canvas.width = 20;
        canvas.height = 20;
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
        const groupCheckbox = document.querySelector('#address_group2');
        let isGrouped = groupCheckbox ? groupCheckbox.checked : false;

        var oldScreenInfo = document.querySelector("#summaryInfo > div.complex_summary_info > div.complex_price_info");
        if (oldScreenInfo) oldScreenInfo.remove();

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
            if (isGrouped)
                strAdditionalInfo += additionalInfos.length > 0 ? "  (" + additionalInfos.join(", ") + ")(" + infos[size]['매매갯수'] + "/" + infos[size]['전세갯수'] + ")" : "  (" + infos[size]['매매갯수'] + "/" + infos[size]['전세갯수'] + ")";
            else
                strAdditionalInfo += additionalInfos.length > 0 ? "  (" + additionalInfos.join(", ") + ")" : "";

            if (isGrouped && isFirst) {
                let multiple = validityCheck[SHINHO_RADIO].value;
                let shinhoDescSource = document.querySelector("#summaryInfo > div.complex_summary_info > div.complex_trade_wrap > div > dl:nth-child(1)");
                if (shinhoDescSource) {
                    let shinhoDesc = shinhoDescSource.cloneNode();
                    shinhoDesc.setAttribute("added", true);
                    let shinhoDt = document.createElement("dt");

                    let greenDescEle = document.createElement("span");
                    greenDescEle.innerHTML = `${SIGN_LOW_VALUE * multiple}%미만`;
                    greenDescEle.style.margin = "0 8px 0 -3px";
                    greenDescEle.classList.add('data');

                    let orangeDescEle = document.createElement("span");
                    orangeDescEle.innerHTML = `${SIGN_MIDDLE_VALUE * multiple}%미만`;
                    orangeDescEle.style.margin = "0 8px 0 -3px";
                    orangeDescEle.classList.add('data');

                    let redDescEle = document.createElement("span");
                    redDescEle.innerHTML = `${SIGN_MIDDLE_VALUE * multiple}%이상`;
                    redDescEle.style.margin = "0 8px 0 -3px";
                    redDescEle.classList.add('data');

                    shinhoDt.appendChild(makeShinhoDot('green'));
                    shinhoDt.appendChild(greenDescEle);
                    shinhoDt.appendChild(makeShinhoDot('orange'));
                    shinhoDt.appendChild(orangeDescEle);
                    shinhoDt.appendChild(makeShinhoDot('red'));
                    shinhoDt.appendChild(redDescEle);

                    shinhoDesc.style.lineHeight = '1px';
                    shinhoDesc.appendChild(shinhoDt);
                    screenInfo.appendChild(shinhoDesc);
                }
                isFirst = false;
            }

            let clonedSource = document.querySelector("#summaryInfo > div.complex_summary_info > div.complex_trade_wrap > div > dl:nth-child(1)");
            if (!clonedSource) continue;

            var cloned = clonedSource.cloneNode(true);
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

        let insertTarget = document.querySelector("#summaryInfo > div.complex_summary_info");
        let insertBefore = document.querySelector("#summaryInfo > div.complex_summary_info > div.complex_detail_link");
        if (insertTarget && insertBefore) {
            insertTarget.insertBefore(screenInfo, insertBefore);
        }
    }

    function sortOnKeys(dict) {
        var tempDict = {};
        let sorted = $('#complexOverviewList > div.list_contents > div.list_fixed > div.list_filter > div > div:nth-child(2) > div > div > ul > li label.checkbox_label')
            .map((idx, item) => item.innerText.replace('㎡', ''));

        let keys = Object.keys(dict);
        sorted.map((idx, item) => {
            keys.map((key) => {
                if (key.indexOf(item) === 0) tempDict[key] = dict[key];
            });
        });
        return tempDict;
    }

    var g_lastSelectedApt = "";

    function addObserverIfDesiredNodeAvailable() {
        var target = document.getElementsByClassName('map_wrap')[0];
        var inDebounce;
        if (!target) {
            console.log('⚠️ map_wrap을 찾을 수 없습니다. 1초 후 재시도...');
            setTimeout(addObserverIfDesiredNodeAvailable, 1000);
            return;
        }

        console.log('✓ map_wrap 발견, Observer 설정 중...');

        for (let key in validityCheck) {
            let obj = validityCheck[key];
            if (!obj.isCreate && document.querySelector('.filter_btn_detail')) {
                createBox(key, obj.type);
            }
        }

        $(document).on('click', (e) => {
            if ($(e.target).parents('a.item_link').length > 0 || e.target.className === 'complex_link')
                setTimeout(() => { $('.detail_panel').css("left", "450px"); }, 500);
        });

        var observer = new MutationObserver(function (mutations) {
            mutations.forEach(function (mutation) {
                [].slice.call(mutation.addedNodes).forEach(function (addedNode) {
                    if (!addedNode.classList ||
                        (!addedNode.classList.contains('infinite_scroll') && !addedNode.classList.contains('item'))) {
                        return;
                    }

                    if (!document.querySelector("#complexTitle")) return;

                    if (document.querySelector("#complexTitle").innerText != g_lastSelectedApt) {
                        document.querySelectorAll("#summaryInfo > div.complex_summary_info > div.complex_trade_wrap > div > dl").forEach(function (ele) {
                            if (ele.hasAttribute("added")) ele.remove();
                        });
                        g_lastSelectedApt = document.querySelector("#complexTitle").innerText;
                    }

                    let scrollArea = document.querySelector("#complexOverviewList > div > div.item_area > div");
                    if (scrollArea) scrollArea.scrollTop = scrollArea.scrollHeight;

                    var runFnc = function () {
                        $('.list_panel').css("width", "450px");
                        $('.detail_panel').css("left", "450px");
                        let result = getPrice_WeolbuStandard();
                        result = sortOnKeys(result);
                        addInfoToScreen(result);
                        let articleList = document.querySelector(".item_list--article");
                        if (articleList) articleList.scrollTop = 0;
                    };

                    if (inDebounce) clearTimeout(inDebounce);
                    inDebounce = setTimeout(runFnc, 500);
                });
            });
        });

        var config = { childList: true, subtree: true };
        observer.observe(target, config);
        console.log('✓ MutationObserver 설정 완료');
    }

    // ========================================
    // 토스트 알림 함수 (alert 대체)
    // ========================================
    function showToast(message, type = 'success', duration = 3000) {
        // 기존 토스트 제거
        const existingToast = document.getElementById('weolbu-toast');
        if (existingToast) existingToast.remove();

        const toast = document.createElement('div');
        toast.id = 'weolbu-toast';

        const bgColor = type === 'success' ? '#4CAF50' :
            type === 'error' ? '#f44336' :
                type === 'warning' ? '#ff9800' : '#2196F3';

        toast.style.cssText = `
            position: fixed;
            top: 20px;
            left: 50%;
            transform: translateX(-50%);
            background: ${bgColor};
            color: white;
            padding: 16px 32px;
            border-radius: 8px;
            font-size: 14px;
            font-weight: 500;
            z-index: 999999;
            box-shadow: 0 4px 20px rgba(0,0,0,0.3);
            animation: slideIn 0.3s ease;
            white-space: pre-line;
            text-align: center;
            max-width: 400px;
        `;

        // 애니메이션 CSS 추가
        if (!document.getElementById('weolbu-toast-styles')) {
            const style = document.createElement('style');
            style.id = 'weolbu-toast-styles';
            style.textContent = `
                @keyframes slideIn {
                    from { opacity: 0; transform: translateX(-50%) translateY(-20px); }
                    to { opacity: 1; transform: translateX(-50%) translateY(0); }
                }
                @keyframes slideOut {
                    from { opacity: 1; transform: translateX(-50%) translateY(0); }
                    to { opacity: 0; transform: translateX(-50%) translateY(-20px); }
                }
            `;
            document.head.appendChild(style);
        }

        toast.textContent = message;
        document.body.appendChild(toast);

        setTimeout(() => {
            toast.style.animation = 'slideOut 0.3s ease';
            setTimeout(() => toast.remove(), 300);
        }, duration);
    }

    // ========================================
    // JSON 내보내기 기능
    // ========================================

    function saveToLocalStorage() {
        console.log('LocalStorage에 데이터 저장 중...');

        const complexName = document.querySelector("#complexTitle") ?
            document.querySelector("#complexTitle").innerText : "Unknown";

        const urlPath = window.location.pathname;
        const complexNo = urlPath.split('/complexes/')[1]?.split('?')[0] || 'unknown';

        const address = document.querySelector("#complexTitle ~ .text") ?
            document.querySelector("#complexTitle ~ .text").innerText : "";

        let totalHouseholds = 0;
        const summaryText = document.querySelector("#summaryInfo")?.innerText || "";
        const householdsMatch = summaryText.match(/(\d+(?:,\d+)*)\s*세대/);
        if (householdsMatch) {
            totalHouseholds = parseInt(householdsMatch[1].replace(/,/g, ''));
        }

        const priceData = getPrice_WeolbuStandard();

        const complexData = {
            metadata: {
                complex_no: complexNo,
                complex_name: complexName,
                address: address,
                total_households: totalHouseholds,
                collected_at: new Date().toISOString(),
                collector: 'chrome_extension'
            },
            listings: []
        };

        for (const areaKey in priceData) {
            const data = priceData[areaKey];
            if (!data) continue;
            if (!data['매매'] && !data['전세']) continue;

            complexData.listings.push({
                area_type: areaKey,
                exclusive_area: data['전용면적'] || extractAreaFromKey(areaKey),
                sale_price: data['매매'] || 0,
                sale_floor: data['매매층'] || '-',
                sale_count: data['매매갯수'] || 0,
                lease_price: data['전세'] || 0,
                lease_floor: data['전세층'] || '-',
                lease_count: data['전세갯수'] || 0,
                gap: data['갭'] || 0,
                lease_rate: data['전세가율'] || '-'
            });
        }

        let savedData = [];
        const storedData = localStorage.getItem('naver_real_estate_data');
        if (storedData) {
            try {
                savedData = JSON.parse(storedData);
            } catch (e) {
                savedData = [];
            }
        }

        const existingIndex = savedData.findIndex(item => item.metadata.complex_no === complexNo);

        if (existingIndex >= 0) {
            savedData[existingIndex] = complexData;
            showToast(`✅ "${complexName}" 데이터 업데이트 완료!\n저장된 아파트: ${savedData.length}개`);
        } else {
            savedData.push(complexData);
            showToast(`✅ "${complexName}" 데이터 저장 완료!\n저장된 아파트: ${savedData.length}개`);
        }

        localStorage.setItem('naver_real_estate_data', JSON.stringify(savedData));
        updateSavedCount();
    }

    function exportAllData() {
        const storedData = localStorage.getItem('naver_real_estate_data');

        if (!storedData) {
            showToast('❌ 저장된 데이터가 없습니다.\n먼저 "💾 저장" 버튼으로 아파트 데이터를 저장하세요.', 'error');
            return;
        }

        let savedData;
        try {
            savedData = JSON.parse(storedData);
        } catch (e) {
            showToast('❌ 저장된 데이터 파싱 오류', 'error');
            return;
        }

        if (savedData.length === 0) {
            showToast('❌ 저장된 데이터가 없습니다.', 'error');
            return;
        }

        const exportData = {
            metadata: {
                export_date: new Date().toISOString(),
                total_complexes: savedData.length,
                complex_names: savedData.map(d => d.metadata.complex_name).join(', ')
            },
            complexes: savedData
        };

        const jsonBlob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(jsonBlob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `naver_all_complexes_${Date.now()}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);

        showToast(`✅ 전체 데이터 내보내기 완료!\n총 ${savedData.length}개 아파트 데이터`);
    }

    function clearSavedData() {
        if (confirm('⚠️ 저장된 모든 데이터를 삭제하시겠습니까?')) {
            localStorage.removeItem('naver_real_estate_data');
            updateSavedCount();
            showToast('✅ 저장된 데이터가 모두 삭제되었습니다.');
        }
    }

    function updateSavedCount() {
        const storedData = localStorage.getItem('naver_real_estate_data');
        let count = 0;
        if (storedData) {
            try {
                count = JSON.parse(storedData).length;
            } catch (e) {
                count = 0;
            }
        }

        const countBadge = document.getElementById('saved-count-badge');
        if (countBadge) {
            countBadge.textContent = count > 0 ? ` (${count})` : '';
        }
    }

    function createButtons() {
        if (document.getElementById('naver-export-container')) return;

        const buttonContainer = document.createElement('div');
        buttonContainer.id = 'naver-export-container';
        buttonContainer.style.cssText = `
            position: fixed;
            top: 70px;
            right: 20px;
            z-index: 10000;
            display: flex;
            flex-direction: column;
            gap: 10px;
        `;

        // 💾 저장 버튼
        const saveButton = document.createElement('button');
        saveButton.innerHTML = '💾 저장<span id="saved-count-badge"></span>';
        saveButton.style.cssText = `
            background: linear-gradient(135deg, #4CAF50 0%, #388E3C 100%);
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 8px;
            font-size: 14px;
            font-weight: bold;
            cursor: pointer;
            box-shadow: 0 4px 15px rgba(76, 175, 80, 0.4);
            transition: all 0.3s ease;
        `;
        saveButton.onclick = saveToLocalStorage;

        // 📥 전체 내보내기 버튼
        const exportButton = document.createElement('button');
        exportButton.innerHTML = '📥 전체 내보내기';
        exportButton.style.cssText = `
            background: linear-gradient(135deg, #9C27B0 0%, #7B1FA2 100%);
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 8px;
            font-size: 14px;
            font-weight: bold;
            cursor: pointer;
            box-shadow: 0 4px 15px rgba(156, 39, 176, 0.4);
            transition: all 0.3s ease;
        `;
        exportButton.onclick = exportAllData;

        // 🗑️ 초기화 버튼
        const clearButton = document.createElement('button');
        clearButton.innerHTML = '🗑️ 초기화';
        clearButton.style.cssText = `
            background: #6c757d;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 6px;
            font-size: 12px;
            cursor: pointer;
            transition: all 0.3s ease;
        `;
        clearButton.onclick = clearSavedData;

        buttonContainer.appendChild(saveButton);
        buttonContainer.appendChild(exportButton);
        buttonContainer.appendChild(clearButton);
        document.body.appendChild(buttonContainer);

        updateSavedCount();
        initClipboard();
        console.log('✓ 버튼 UI 생성 완료');
    }

    // 초기화
    function init() {
        console.log('✓ 네이버 부동산 분석 도우미 초기화...');
        createButtons();
        addObserverIfDesiredNodeAvailable();
    }

    // 페이지 로드 시 실행
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

    // MutationObserver로 페이지 변경 감지
    const exportObserver = new MutationObserver(function (mutations) {
        mutations.forEach(function (mutation) {
            if (mutation.addedNodes.length > 0) {
                const complexTitle = document.querySelector("#complexTitle");
                if (complexTitle && !document.getElementById('naver-export-container')) {
                    setTimeout(createButtons, 500);
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

    console.log('✓ 네이버 부동산 분석 도우미 로드 완료 (Chrome Extension)');

})();

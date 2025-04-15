<script>
    // @ts-nocheck

    // import search_icon from "$lib/static/images/search.svg";
    // import eye_icon from "$lib/static/images/eye.svg";
    // import annotation_icon from "$lib/static/images/blockquote.svg";
    // import unreviewed_annotation_icon from "$lib/static/images/warning.svg";
    // import pyong_icon from "$lib/static/images/bolt.svg";
    // import release_date_icon from "$lib/static/images/calendar.svg";
    import { onMount } from "svelte";
    import "./style.css";
    import { base } from "$app/paths";
    import { CorsProxyAddr } from "$lib";

    let { links = {} } = $props();

    const number_formatter = new Intl.NumberFormat(
        navigator.language ?? "en-US",
        { notation: "compact", maximumFractionDigits: 2 },
    );

    let song_results = $state([]);
    let lyric_results = $state([]);

    let search_input_value = ""; // Store the input value
    let search_results_loading;
    let search_results_container;
    let search_timeout = null; // Used for debounce
    let is_request_in_progress = false; // Flag to check if request is in progress

    function highlightRanges(text, ranges) {
        ranges.sort((a, b) => b.start - a.start);

        for (const { start, end } of ranges) {
            text = text.slice(0, end) + "</span>" + text.slice(end);
            text =
                text.slice(0, start) +
                "<span class='lyric_result_highlight'>" +
                text.slice(start);
        }

        return text;
    }

    onMount(() => {
        const search_input = document.getElementById("searchbox");
        search_results_loading = document.getElementById("search_results_loading");
        search_results_container =
            document.getElementById("search_results") ?? new HTMLElement();
        
        search_input.addEventListener("input", (e) => {
            search_input_value = e.target.value; // Capture the input value on typing
            search_results_loading.style.display = "block"; // Show the loading message
            search_results_container.style.display = "block"; // Keep the results container visible while typing

            // Clear any previous timeout (debounce)
            if (search_timeout) {
                clearTimeout(search_timeout);
            }

            // Set a new timeout for search, only trigger after 500ms of inactivity
            search_timeout = setTimeout(() => {
                performSearch();
            }, 500);
        });

        // Function to perform search
        async function performSearch() {
            // If no input or request is already in progress, skip
            if (!search_input_value.trim() || is_request_in_progress) {
                return;
            }

            // Set flag to prevent duplicate requests
            is_request_in_progress = true;

            search_results_loading.innerText = `Querying "${search_input_value}"...`;
            search_results_loading.style.backgroundColor = "blue";

            try {
                const parsedResponse = await (
                    await fetch(
                        `${CorsProxyAddr}${encodeURIComponent('https://genius.com/api/search/multi?q=')}${encodeURIComponent(search_input_value)}`
                    )
                ).json();

                console.log(parsedResponse);

                song_results = [];
                lyric_results = [];

                parsedResponse["response"]["sections"].forEach((res) => {
                    if (res["type"] == "song") {
                        song_results = res["hits"];
                    }
                    if (res["type"] == "lyric") {
                        let hits = [];
                        res["hits"].forEach((hit) => {
                            const lyric = hit["highlights"][0]["value"];
                            let lyric_array = highlightRanges(lyric, hit["highlights"][0]["ranges"]).replaceAll("\n", "<br>");
                            hit = { __lyric: lyric_array, ...hit };
                            hits.push(hit);
                        });
                        lyric_results = hits;
                    }
                });

                if (song_results.length === 0 && lyric_results.length === 0) {
                    search_results_loading.innerText = `No results found for "${search_input_value}"`;
                    search_results_loading.style.backgroundColor = "red";
                } else {
                    search_results_loading.innerText = `Loaded results for "${search_input_value}"!`;
                    search_results_loading.style.backgroundColor = "darkgreen";
                }
            } catch (error) {
                search_results_loading.innerText = `Error occurred during search`;
                search_results_loading.style.backgroundColor = "red";
            } finally {
                // Reset flag once the request is complete
                is_request_in_progress = false;
            }
        }

        document.addEventListener("click", () => {
            search_results_container.style.display = "none";
        });

        search_results_container.style.left = `${search_input.parentElement.offsetLeft}px`;
    });
</script>

    
<header>
    <div id="left">
        <a class="item" href={base}>OpenGenius</a>
        <div class="item no_hover_change no_padding_no_margin" id="search">
            <!-- Edge does not respect autocomplete="off", only "aria-autocomplete" -->
            <input
                type="text"
                class="no_padding_no_margin"
                name="search"
                id="searchbox"
                placeholder="Search"
                autocomplete="off"
                aria-autocomplete="none"
            />
            <button
                type="button"
                id="search_button"
                class="no_padding_no_margin"
            >
                <!-- <img
                    src={search_icon}
                    alt="Search Icon"
                    style="align-self: center; height: 70%; aspect-ratio: 1; transform: translateY(13%)"
                /> -->
                <svg
                    xmlns="http://www.w3.org/2000/svg"
                    style="align-self: center; height: 70%; aspect-ratio: 1; transform: translateY(13%)"
                    fill="currentColor"
                    class="bi bi-search"
                    viewBox="0 0 16 16"
                >
                    <path
                        d="M11.742 10.344a6.5 6.5 0 1 0-1.397 1.398h-.001q.044.06.098.115l3.85 3.85a1 1 0 0 0 1.415-1.414l-3.85-3.85a1 1 0 0 0-.115-.1zM12 6.5a5.5 5.5 0 1 1-11 0 5.5 5.5 0 0 1 11 0"
                    />
                </svg>
            </button>
        </div>
    </div>
    <div id="right">
        {#each Object.entries(links) as [text, href]}
            <a {href} class="item">{text}</a>
        {/each}
        <a class="item" href="#top">GitHub</a>
    </div>
    <ul class="no_padding_no_margin" id="search_results">
        <li
            id="search_results_loading"
            class="loading_status_loaded loading_status_loading"
        >
            Loading...
        </li>
        <li class="search_result_type_label">Songs</li>
        {#each song_results as result}
            <!-- svelte-ignore a11y_no_noninteractive_element_interactions -->
            <!-- svelte-ignore a11y_click_events_have_key_events -->
            <li
                class="search_result_item"
                onclick={() => {
                    window.location.href = `${base}/lyrics?path=${encodeURIComponent(result["result"]["path"])}`;
                }}
            >
                <img
                    src={result["result"]["header_image_thumbnail_url"]}
                    class="search_img"
                    alt=""
                />
                <div class="search_result_right_section">
                    <div class="search_result_right_top">
                        <p class="no_padding_no_margin song_title">
                            {result["result"]["title"]}
                        </p>
                        <p class="no_padding_no_margin artist">
                            {result["result"]["primary_artist_names"]}
                        </p>
                    </div>
                    <div class="search_result_right_bottom">
                        <div
                            class="search_result_statistic"
                            title={`${!isNaN(result["result"]["stats"]["pageviews"]) ? result["result"]["stats"]["pageviews"].toLocaleString(navigator.language) : (0).toLocaleString(navigator.language)} page views`}
                        >
                            <svg
                                fill="currentColor"
                                xmlns="http://www.w3.org/2000/svg"
                                height="15px"
                                width="15px"
                                viewBox="0 0 22 15.45"
                            >
                                <path
                                    d="M11 2c4 0 7.26 3.85 8.6 5.72-1.34 1.87-4.6 5.73-8.6 5.73S3.74 9.61 2.4 7.73C3.74 5.86 7 2 11 2m0-2C4.45 0 0 7.73 0 7.73s4.45 7.73 11 7.73 11-7.73 11-7.73S17.55 0 11 0z"
                                ></path>
                                <path
                                    d="M11 5a2.73 2.73 0 1 1-2.73 2.73A2.73 2.73 0 0 1 11 5m0-2a4.73 4.73 0 1 0 4.73 4.73A4.73 4.73 0 0 0 11 3z"
                                ></path>
                            </svg>
                            <p class="inline no_padding_no_margin">
                                {!isNaN(result["result"]["stats"]["pageviews"])
                                    ? number_formatter.format(
                                          result["result"]["stats"][
                                              "pageviews"
                                          ],
                                      )
                                    : number_formatter.format("0")}
                            </p>
                        </div>
                        {#if result["result"]["annotation_count"] > 0}
                            <div
                                class="search_result_statistic"
                                title="Total Annotations"
                            >
                                <svg
                                    fill="currentColor"
                                    xmlns="http://www.w3.org/2000/svg"
                                    viewBox="0 0 22 22"
                                    width="15px"
                                    height="15px"
                                >
                                    <path
                                        d="M15 10.47h1.7v4.3h-4.4v-3.75c0-2.78.63-5.3 4.39-5.52v2.22c-1.26 0-1.69.88-1.69 2.75zm-7 0h1.7v4.3H5.3v-3.75c0-2.78.63-5.3 4.39-5.52v2.22C8.43 7.72 8 8.6 8 10.47z"
                                    ></path>
                                    <path
                                        d="M20.09 1.91v18.18H1.91V1.91h18.18M22 0H0v22h22V0z"
                                    ></path>
                                </svg>
                                <p class="inline no_padding_no_margin">
                                    {result["result"]["annotation_count"]}
                                </p>
                            </div>
                        {/if}
                        {#if result["result"]["stats"]["unreviewed_annotations"] > 0}
                            <div
                                class="search_result_statistic"
                                title="Unreviewed Annotations"
                            >
                                <svg
                                    viewBox="0 0 22 19.8"
                                    height="15px"
                                    width="15px"
                                    fill="currentColor"
                                    xmlns="http://www.w3.org/2000/svg"
                                    ><path
                                        d="m11 4.12 7.6 13.68H3.4L11 4.12M11 0 0 19.8h22L11 0z"
                                    ></path><path
                                        d="M10 8.64h2v4.51h-2zm1 5.45a1.13 1.13 0 0 1 1.13 1.15A1.13 1.13 0 1 1 11 14.09z"
                                    ></path></svg
                                >
                                <p class="inline no_padding_no_margin">
                                    {result["result"]["stats"][
                                        "unreviewed_annotations"
                                    ]}
                                </p>
                            </div>
                        {/if}
                        {#if result["result"]["pyongs_count"] > 0}
                            <div
                                class="search_result_statistic"
                                title="Total Pyongs"
                            >
                                <svg
                                    width="15px"
                                    height="15px"
                                    viewBox="0 0 11.37 22"
                                    fill="currentColor"
                                    xmlns="http://www.w3.org/2000/svg"
                                    ><path
                                        d="M0 7l6.16-7 3.3 7H6.89S5.5 12.1 5.5 12.17h5.87L6.09 22l.66-7H.88l2.89-8z"
                                    ></path></svg
                                >
                                <p class="inline no_padding_no_margin">
                                    {result["result"]["pyongs_count"]}
                                </p>
                            </div>
                        {/if}
                        <div
                            class="search_result_statistic"
                            title="Release Date"
                        >
                            <svg
                                width="15px"
                                height="15px"
                                fill="currentColor"
                                xmlns="http://www.w3.org/2000/svg"
                                viewBox="0 0 18 18"
                                ><path
                                    d="M15.923 1.385h-2.77V0H11.77v1.385H6.231V0H4.846v1.385h-2.77c-.76 0-1.384.623-1.384 1.384v13.846c0 .762.623 1.385 1.385 1.385h13.846c.762 0 1.385-.623 1.385-1.385V2.77c0-.761-.623-1.384-1.385-1.384Zm0 15.23H2.077V6.923h13.846v9.692Zm0-11.077H2.077V2.77h2.77v1.385H6.23V2.769h5.538v1.385h1.385V2.769h2.77v2.77Z"
                                ></path></svg
                            >
                            <p class="inline no_padding_no_margin">
                                {result["result"][
                                    "release_date_with_abbreviated_month_for_display"
                                ]}
                            </p>
                        </div>
                    </div>
                </div>
            </li>
        {:else}
            <li style="margin-left: 5px;">No Song Results Found</li>
        {/each}

        <li class="search_result_type_label">Lyrics</li>
        {#each lyric_results as result}
            <li class="search_result_item">
                <img
                    src={result["result"]["header_image_thumbnail_url"]}
                    class="search_img"
                    alt=""
                />
                <div class="search_result_right_section">
                    <div class="search_result_right_top">
                        <p class="no_padding_no_margin song_title">
                            {result["result"]["title"]}
                        </p>
                        <p class="no_padding_no_margin artist">
                            {result["result"]["primary_artist_names"]}
                        </p>
                        <p class="no_padding_no_margin lyric_result">
                            {@html result["__lyric"]}
                        </p>
                    </div>
                    <div class="search_result_right_bottom">
                        <div
                            class="search_result_statistic"
                            title={`${!isNaN(result["result"]["stats"]["pageviews"]) ? result["result"]["stats"]["pageviews"].toLocaleString(navigator.language) : (0).toLocaleString(navigator.language)} page views`}
                        >
                            <svg
                                fill="currentColor"
                                xmlns="http://www.w3.org/2000/svg"
                                height="15px"
                                width="15px"
                                viewBox="0 0 22 15.45"
                            >
                                <path
                                    d="M11 2c4 0 7.26 3.85 8.6 5.72-1.34 1.87-4.6 5.73-8.6 5.73S3.74 9.61 2.4 7.73C3.74 5.86 7 2 11 2m0-2C4.45 0 0 7.73 0 7.73s4.45 7.73 11 7.73 11-7.73 11-7.73S17.55 0 11 0z"
                                ></path>
                                <path
                                    d="M11 5a2.73 2.73 0 1 1-2.73 2.73A2.73 2.73 0 0 1 11 5m0-2a4.73 4.73 0 1 0 4.73 4.73A4.73 4.73 0 0 0 11 3z"
                                ></path>
                            </svg>
                            <p class="inline no_padding_no_margin">
                                {!isNaN(result["result"]["stats"]["pageviews"])
                                    ? number_formatter.format(
                                          result["result"]["stats"][
                                              "pageviews"
                                          ],
                                      )
                                    : number_formatter.format("0")}
                            </p>
                        </div>
                        {#if result["result"]["annotation_count"] > 0}
                            <div
                                class="search_result_statistic"
                                title="Total Annotations"
                            >
                                <svg
                                    fill="currentColor"
                                    xmlns="http://www.w3.org/2000/svg"
                                    viewBox="0 0 22 22"
                                    height="15px"
                                    width="15px"
                                >
                                    <path
                                        d="M15 10.47h1.7v4.3h-4.4v-3.75c0-2.78.63-5.3 4.39-5.52v2.22c-1.26 0-1.69.88-1.69 2.75zm-7 0h1.7v4.3H5.3v-3.75c0-2.78.63-5.3 4.39-5.52v2.22C8.43 7.72 8 8.6 8 10.47z"
                                    ></path>
                                    <path
                                        d="M20.09 1.91v18.18H1.91V1.91h18.18M22 0H0v22h22V0z"
                                    ></path>
                                </svg>
                                <p class="inline no_padding_no_margin">
                                    {result["result"]["annotation_count"]}
                                </p>
                            </div>
                        {/if}
                        {#if result["result"]["stats"]["unreviewed_annotations"] > 0}
                            <div
                                class="search_result_statistic"
                                title="Unreviewed Annotations"
                            >
                                <svg
                                    viewBox="0 0 22 19.8"
                                    fill="currentColor"
                                    xmlns="http://www.w3.org/2000/svg"
                                    height="15px"
                                    width="15px"
                                    ><path
                                        d="m11 4.12 7.6 13.68H3.4L11 4.12M11 0 0 19.8h22L11 0z"
                                    ></path><path
                                        d="M10 8.64h2v4.51h-2zm1 5.45a1.13 1.13 0 0 1 1.13 1.15A1.13 1.13 0 1 1 11 14.09z"
                                    ></path></svg
                                >
                                <p class="inline no_padding_no_margin">
                                    {result["result"]["stats"][
                                        "unreviewed_annotations"
                                    ]}
                                </p>
                            </div>
                        {/if}
                        {#if result["result"]["pyongs_count"] > 0}
                            <div
                                class="search_result_statistic"
                                title="Total Pyongs"
                            >
                                <svg
                                    height="15px"
                                    width="15px"
                                    viewBox="0 0 11.37 22"
                                    fill="currentColor"
                                    xmlns="http://www.w3.org/2000/svg"
                                    ><path
                                        d="M0 7l6.16-7 3.3 7H6.89S5.5 12.1 5.5 12.17h5.87L6.09 22l.66-7H.88l2.89-8z"
                                    ></path></svg
                                >
                                <p class="inline no_padding_no_margin">
                                    {result["result"]["pyongs_count"]}
                                </p>
                            </div>
                        {/if}
                        <div
                            class="search_result_statistic"
                            title="Release Date"
                        >
                            <svg
                                width="15px"
                                height="15px"
                                fill="currentColor"
                                xmlns="http://www.w3.org/2000/svg"
                                viewBox="0 0 18 18"
                                ><path
                                    d="M15.923 1.385h-2.77V0H11.77v1.385H6.231V0H4.846v1.385h-2.77c-.76 0-1.384.623-1.384 1.384v13.846c0 .762.623 1.385 1.385 1.385h13.846c.762 0 1.385-.623 1.385-1.385V2.77c0-.761-.623-1.384-1.385-1.384Zm0 15.23H2.077V6.923h13.846v9.692Zm0-11.077H2.077V2.77h2.77v1.385H6.23V2.769h5.538v1.385h1.385V2.769h2.77v2.77Z"
                                ></path></svg
                            >
                            <p class="inline no_padding_no_margin">
                                {result["result"][
                                    "release_date_with_abbreviated_month_for_display"
                                ]}
                            </p>
                        </div>
                    </div>
                </div>
            </li>
        {:else}
            <li style="margin-left: 5px;">No Lyric Results Found</li>
        {/each}
    </ul>
</header>

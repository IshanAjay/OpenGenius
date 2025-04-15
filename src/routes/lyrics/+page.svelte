<script>
    // @ts-nocheck
    import TopMenuBar from "$lib/TopMenuBar/TopMenuBar.svelte";
    import { onMount } from "svelte";
    import "./style.css";
    import { base } from "$app/paths";
    import { CorsProxyAddr } from "$lib";
    let state = $state(null);

    function extractInfoFromDfpKv(part, first_value_only) {
        let res = null;
        $state.snapshot(state)["songPage"]["dfpKv"].every((info) => {
            if (info["name"] == part) {
                if (first_value_only) {
                    res = info["values"][0];
                    return false;
                }
                res = info["values"];
                return false;
            }
            return true;
        });
        return res;
    }
    function extractInfoFromTrackingData(part) {
        let res = null;
        $state.snapshot(state)["songPage"]["trackingData"].every((info) => {
            if (info["key"] == part) {
                res = info["value"];
                return false;
            }
            return true;
        });
        return res;
    }
    onMount(async () => {
        const path = decodeURIComponent(
            new URLSearchParams(new URL(window.location.href).search).get(
                "path",
            ) ?? "",
        );
        let response = await (
            await fetch(
                `${CorsProxyAddr}${encodeURIComponent("https://genius.com")}${encodeURIComponent(path)}`,
            )
        ).text();
        const state_setter = response.match(/window\.__PRELOADED_STATE__.+;/);
        eval(
            (state_setter ??
                "throw new SyntaxError('window.__PRELOADED_STATE__ not found! Genius.com may have updated their site...')")[0],
        );
        state = window.__PRELOADED_STATE__ ?? {};
    });
    $effect(() => {
        // Format lyrics
        if (state == null) {
            return;
        }
        const lyrics_container = document.getElementById("lyrics_container");
        lyrics_container.innerHTML +=
            state["songPage"]["lyricsData"]["body"]["html"];
        const lyrics_container_inner_paragraph =
            lyrics_container.getElementsByTagName("p")[0];
        function handleAnchorsRecursively(elem) {
            for (let child of elem.children) {
                // Only element nodes
                if (child.nodeName === "A") {
                    if (child.getAttribute("data-real-link") != "true") {
                        child.removeAttribute("href");
                    }
                    child.addEventListener("mouseenter", () => {
                        Array.from(lyrics_container_inner_paragraph.childNodes)
                            .filter(
                                (item) =>
                                    item.nodeName != "#text" &&
                                    item.getAttribute("data-id") ===
                                        child.getAttribute("data-id"),
                            )
                            .forEach((item) => {
                                item.classList.add("highlight");
                            });
                    });

                    child.addEventListener("mouseleave", () => {
                        Array.from(lyrics_container_inner_paragraph.childNodes)
                            .filter(
                                (item) =>
                                    item.nodeName != "#text" &&
                                    item.getAttribute("data-id") ===
                                        child.getAttribute("data-id"),
                            )
                            .forEach((item) => {
                                item.classList.remove("highlight");
                            });
                    });

                    child.addEventListener("click", async () => {
                        const annotation_bar_spacer = document.getElementById(
                            "annotation_bar_spacer",
                        );
                        annotation_bar_spacer.style.height = `${Number(child.offsetTop) - (Number(document.getElementsByTagName("header")[0].offsetHeight) + Number(document.getElementById("top_section").offsetHeight))}px`;
                        const api_response = await (
                            await fetch(
                                `${CorsProxyAddr}${encodeURIComponent("https://genius.com/api/referents/")}${child.getAttribute("data-id")}${encodeURIComponent("?text_format=html%2Cmarkdown")}`,
                            )
                        ).json();
                        const annotation_bar_quote = document.getElementById(
                            "annotation_bar_quote",
                        );
                        annotation_bar_quote.innerText = api_response['response']['referent']['range']['content']
                        const annotation_bar =
                            document.getElementById("annotation_bar");
                        const annotation_bar_content = document.getElementById(
                            "annotation_bar_content",
                        );
                        const annotation_bar_verified = document.getElementById("annotation_bar_credibility")
                        const credibility = api_response[
                            "response"
                        ]["referent"]["classification"]
                        if (credibility==="cosigned") {
                            annotation_bar_verified.style.backgroundColor = 'darkgreen'
                            annotation_bar_verified.style.color = 'white'
                            annotation_bar_verified.style.display = 'block'
                            annotation_bar_verified.innerText = `Cosigned by ${api_response["response"]["referent"]["annotations"][0]["cosigned_by"][0]["name"]}`
                        } else if (credibility==="verified") {
                            annotation_bar_verified.style.backgroundColor = 'darkgreen'
                            annotation_bar_verified.style.display = 'block'
                            annotation_bar_verified.style.color = 'white'
                            annotation_bar_verified.innerText = `Verified by ${api_response["response"]["referent"]["annotations"][0]["verified_by"]["name"]}`
                        } else if (credibility==="unreviewed") {
                            annotation_bar_verified.style.backgroundColor = 'red'
                            annotation_bar_verified.style.display = 'block'
                            annotation_bar_verified.style.color = 'white'
                            annotation_bar_verified.innerText = `This Annotation is Unreviewed`
                        } else {
                            annotation_bar_verified.style.display = 'none'
                        }
                        annotation_bar_content.innerHTML = api_response[
                            "response"
                        ]["referent"]["annotations"][0]["body"]["html"]
                            .replaceAll(
                                /(?<=<a.+href=\")https?\:\/\/(www\.)?genius\.com\/(.+-lyrics)(?=\")/g,
                                `${base}/lyrics?path=%2F$2`,
                            ) // Replace links that go to Genius lyric pages with OpenGenius equivalents
                            .replaceAll(
                                /<iframe(?=.+src="https?:\/\/(?:www\.)?youtube\.com\/embed)/g,
                                '<iframe sandbox="allow-scripts allow-same-origin allow-presentation"',
                            );
                    });

                    if (
                        child.getAttribute("data-classification") ===
                        "unreviewed"
                    ) {
                        child.classList.add("unreviewed");
                    }

                    child.style.cursor = "pointer";
                }

                // Recurse into the child
                if (child.children.length > 0) {
                    handleAnchorsRecursively(child);
                }
            }
        }

        handleAnchorsRecursively(lyrics_container);
    });
</script>

<TopMenuBar />

{#if state != null}
    <main>
        <div id="top_section">
            <div id="left_section">
                <img
                    loading="lazy"
                    src={state["entities"]["songs"][state["songPage"]["song"]][
                        "headerImageThumbnailUrl"
                    ]}
                    alt="Blinding Lights"
                    id="song_cover_img_top"
                />
            </div>
            <div id="right_section">
                <div id="right_section_top">
                    <h1 class="no_padding_no_margin" id="song_title">
                        {extractInfoFromTrackingData("Title")}
                    </h1>
                    <p class="no_padding_no_margin" id="artist">
                        {extractInfoFromTrackingData("Primary Artists").join(
                            ", ",
                        )}
                    </p>
                    <!-- <p class="no_padding_no_margin">
                        Track 4 on <em>The Highlights: Deluxe</em>
                    </p> -->
                </div>
                <div id="right_section_bottom">
                    <p id="about_container" class="no_padding_no_margin">
                        {@html state["entities"]["annotations"][
                            Object.keys(state["entities"]["annotations"])[0]
                        ]["body"]["html"]
                            .replaceAll(
                                /<iframe(?=.+src="https?:\/\/(?:www\.)?youtube\.com\/embed)/g,
                                '<iframe sandbox="allow-scripts allow-same-origin allow-presentation"',
                            ) // Replace YouTube embeds with 'enhanced privacy mode'
                            .replaceAll(
                                /(?<=<a.+href=\")https?\:\/\/(www\.)?genius\.com\/(.+-lyrics)(?=\")/g,
                                `${base}/lyrics?path=%2F$2`,
                            )}
                    </p>
                    <a href="#about">Read more...</a>
                    <div id="stats_bar" style="margin-top: 10px">
                        <div class="statistic">
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
                                {[
                                    "January",
                                    "February",
                                    "March",
                                    "April",
                                    "May",
                                    "June",
                                    "July",
                                    "August",
                                    "September",
                                    "October",
                                    "November",
                                    "December",
                                ][
                                    new Date(
                                        extractInfoFromTrackingData(
                                            "Release Date",
                                        ),
                                    ).getMonth()
                                ]}
                                {new Date(
                                    extractInfoFromTrackingData("Release Date"),
                                ).getDate()}, {new Date(
                                    extractInfoFromTrackingData("Release Date"),
                                ).getFullYear()}
                            </p>
                        </div>
                        <!-- <div class="statistic">
                            <svg
                                height="15px"
                                width="15px"
                                xmlns="http://www.w3.org/2000/svg"
                                fill="currentColor"
                                viewBox="0 0 18 18"
                                ><path
                                    fill-rule="evenodd"
                                    d="M4 16.483A9 9 0 1 0 14 1.518 9 9 0 0 0 4 16.483Zm.714-13.897a7.714 7.714 0 1 1 8.572 12.828A7.714 7.714 0 0 1 4.714 2.586Zm3.643 6.678 3.594 3.593.906-.906L9.643 8.73V3.214H8.357v6.05Z"
                                    clip-rule="evenodd"
                                ></path></svg
                            >
                            <p class="inline no_padding_no_margin">
                                3 Current Viewers
                            </p>
                        </div> -->
                        <div class="statistic">
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
                                {Number(
                                    extractInfoFromDfpKv("pageviews", true),
                                ).toLocaleString()} Total Views
                            </p>
                        </div>
                        <div class="statistic">
                            <svg
                                viewBox="0 0 11.37 22"
                                height="15px"
                                width="15px"
                                fill="currentColor"
                                xmlns="http://www.w3.org/2000/svg"
                                ><path
                                    d="M0 7l6.16-7 3.3 7H6.89S5.5 12.1 5.5 12.17h5.87L6.09 22l.66-7H.88l2.89-8z"
                                ></path></svg
                            >
                            <!-- <p class="inline no_padding_no_margin">
                                3,389 Pyongs
                            </p> -->
                        </div>
                    </div>
                </div>
            </div>
        </div>
        <div id="lyrics_section">
            <p id="lyrics_container" class="no_padding_no_margin"></p>
            <div id="annotation_bar">
                <div id="annotation_bar_spacer"></div>
                <div id="annotation_bar_quote"></div>
                <div id="annotation_bar_credibility" style="display: none;"></div>
                <div id="annotation_bar_content"></div>
            </div>
        </div>
        <div id="about">
            <h1>About</h1>
            <p>
                {@html state["entities"]["annotations"][
                    Object.keys(state["entities"]["annotations"])[0]
                ]["body"]["html"]
                    .replaceAll(
                        /<iframe(?=.+src="https?:\/\/(?:www\.)?youtube\.com\/embed)/g,
                        '<iframe sandbox="allow-scripts allow-same-origin allow-presentation"',
                    )
                    .replaceAll(
                        /(?<=<a.+href=\")https?\:\/\/(www\.)?genius\.com\/(.+-lyrics)(?=\")/g,
                        `${base}/lyrics?path=%2F$2`,
                    )}
            </p>
        </div>
    </main>
{:else}
<main>
    Loading...
</main>
{/if}
/* eslint-disable */
import { getLocale, experimentalStaticLocale } from "../runtime.js"

/** @typedef {import('../runtime.js').LocalizedString} LocalizedString */
/** @typedef {{}} App_NameInputs */
/** @typedef {{}} Nav_HomeInputs */
/** @typedef {{}} Nav_SearchInputs */
/** @typedef {{}} Nav_MessagesInputs */
/** @typedef {{}} Nav_AppsInputs */
/** @typedef {{}} Nav_ProfileInputs */
/** @typedef {{}} Drawer_CreditsInputs */
/** @typedef {{}} Drawer_MurakumoInputs */
/** @typedef {{}} Drawer_Hc_TasksInputs */
/** @typedef {{}} Drawer_TermsInputs */
/** @typedef {{}} Drawer_PrivacyInputs */
/** @typedef {{}} Drawer_FeedbackInputs */
/** @typedef {{}} Drawer_HelpInputs */
/** @typedef {{}} Drawer_HistoryInputs */
/** @typedef {{}} Drawer_SettingsInputs */
/** @typedef {{}} Drawer_Sign_OutInputs */
/** @typedef {{}} Cookie_TitleInputs */
/** @typedef {{}} Cookie_DescriptionInputs */
/** @typedef {{}} Cookie_DeclineInputs */
/** @typedef {{}} Cookie_AcceptInputs */
/** @typedef {{}} Inference_Important_NoticeInputs */
/** @typedef {{}} Inference_Scroll_PromptInputs */
/** @typedef {{}} Inference_Agree_CheckboxInputs */
/** @typedef {{}} Inference_DeclineInputs */
/** @typedef {{}} Inference_AgreeInputs */
/** @typedef {{}} Content_Label_BackInputs */
/** @typedef {{}} Content_Label_AgreeInputs */
/** @typedef {{}} Profile_Spam_BlockInputs */
/** @typedef {{ threshold: NonNullable<unknown> }} Profile_Spam_Block_DescInputs */
/** @typedef {{}} Profile_PostsInputs */
/** @typedef {{}} Profile_FollowersInputs */
/** @typedef {{}} Profile_FollowingInputs */
/** @typedef {{}} Profile_FollowInputs */
/** @typedef {{}} Profile_UnfollowInputs */
/** @typedef {{}} Profile_MessageInputs */
/** @typedef {{}} Profile_EditInputs */
/** @typedef {{}} Search_ActorsInputs */
/** @typedef {{}} Search_PostsInputs */
/** @typedef {{}} Search_PeopleInputs */
/** @typedef {{}} Search_PlaceholderInputs */
/** @typedef {{}} Feed_DiscoverInputs */
/** @typedef {{}} Feed_FollowingInputs */
/** @typedef {{}} Feed_EmptyInputs */
/** @typedef {{}} Feed_LoadingInputs */
/** @typedef {{}} Feed_Error_RetryInputs */
/** @typedef {{}} Compose_PlaceholderInputs */
/** @typedef {{}} Compose_PostInputs */
/** @typedef {{}} Compose_CancelInputs */
/** @typedef {{}} Convo_New_MessageInputs */
/** @typedef {{}} Convo_EmptyInputs */
/** @typedef {{}} Common_LoadingInputs */
/** @typedef {{}} Common_ErrorInputs */
/** @typedef {{}} Common_RetryInputs */
/** @typedef {{}} Common_SaveInputs */
/** @typedef {{}} Common_CancelInputs */
/** @typedef {{}} Common_DeleteInputs */
/** @typedef {{}} Common_ConfirmInputs */
/** @typedef {{}} Common_BackInputs */
/** @typedef {{}} Common_CloseInputs */
/** @typedef {{ count: NonNullable<unknown> }} Common_ViewsInputs */
import * as __en from "./en.js"
import * as __ar from "./ar.js"
import * as __as from "./as.js"
import * as __bn from "./bn.js"
import * as __de from "./de.js"
import * as __es from "./es.js"
import * as __fa from "./fa.js"
import * as __fr from "./fr.js"
import * as __gu from "./gu.js"
import * as __he from "./he.js"
import * as __hi from "./hi.js"
import * as __id from "./id.js"
import * as __ja from "./ja.js"
import * as __kn from "./kn.js"
import * as __ko from "./ko.js"
import * as __ku from "./ku.js"
import * as __ml from "./ml.js"
import * as __mr from "./mr.js"
import * as __ne from "./ne.js"
import * as __or from "./or.js"
import * as __pa from "./pa.js"
import * as __pt from "./pt.js"
import * as __ru from "./ru.js"
import * as __si from "./si.js"
import * as __ta from "./ta.js"
import * as __te from "./te.js"
import * as __th from "./th.js"
import * as __tr from "./tr.js"
import * as __ur from "./ur.js"
import * as __vi from "./vi.js"
import * as __zh_hans1 from "./zh-Hans.js"
/**
* | output |
* | --- |
* | "YORO" |
*
* @param {App_NameInputs} inputs
* @param {{ locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }} options
* @returns {LocalizedString}
*/
export const app_name = /** @type {((inputs?: App_NameInputs, options?: { locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }) => LocalizedString) & import('../runtime.js').MessageMetadata<App_NameInputs, { locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }, {}>} */ ((inputs = {}, options = {}) => {
	const locale = experimentalStaticLocale ?? options.locale ?? getLocale()
	if (locale === "en") return __en.app_name(inputs)
	if (locale === "ar") return __ar.app_name(inputs)
	if (locale === "as") return __as.app_name(inputs)
	if (locale === "bn") return __bn.app_name(inputs)
	if (locale === "de") return __de.app_name(inputs)
	if (locale === "es") return __es.app_name(inputs)
	if (locale === "fa") return __fa.app_name(inputs)
	if (locale === "fr") return __fr.app_name(inputs)
	if (locale === "gu") return __gu.app_name(inputs)
	if (locale === "he") return __he.app_name(inputs)
	if (locale === "hi") return __hi.app_name(inputs)
	if (locale === "id") return __id.app_name(inputs)
	if (locale === "ja") return __ja.app_name(inputs)
	if (locale === "kn") return __kn.app_name(inputs)
	if (locale === "ko") return __ko.app_name(inputs)
	if (locale === "ku") return __ku.app_name(inputs)
	if (locale === "ml") return __ml.app_name(inputs)
	if (locale === "mr") return __mr.app_name(inputs)
	if (locale === "ne") return __ne.app_name(inputs)
	if (locale === "or") return __or.app_name(inputs)
	if (locale === "pa") return __pa.app_name(inputs)
	if (locale === "pt") return __pt.app_name(inputs)
	if (locale === "ru") return __ru.app_name(inputs)
	if (locale === "si") return __si.app_name(inputs)
	if (locale === "ta") return __ta.app_name(inputs)
	if (locale === "te") return __te.app_name(inputs)
	if (locale === "th") return __th.app_name(inputs)
	if (locale === "tr") return __tr.app_name(inputs)
	if (locale === "ur") return __ur.app_name(inputs)
	if (locale === "vi") return __vi.app_name(inputs)
	return __zh_hans1.app_name(inputs)
});
/**
* | output |
* | --- |
* | "Home" |
*
* @param {Nav_HomeInputs} inputs
* @param {{ locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }} options
* @returns {LocalizedString}
*/
export const nav_home = /** @type {((inputs?: Nav_HomeInputs, options?: { locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }) => LocalizedString) & import('../runtime.js').MessageMetadata<Nav_HomeInputs, { locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }, {}>} */ ((inputs = {}, options = {}) => {
	const locale = experimentalStaticLocale ?? options.locale ?? getLocale()
	if (locale === "en") return __en.nav_home(inputs)
	if (locale === "ar") return __ar.nav_home(inputs)
	if (locale === "as") return __as.nav_home(inputs)
	if (locale === "bn") return __bn.nav_home(inputs)
	if (locale === "de") return __de.nav_home(inputs)
	if (locale === "es") return __es.nav_home(inputs)
	if (locale === "fa") return __fa.nav_home(inputs)
	if (locale === "fr") return __fr.nav_home(inputs)
	if (locale === "gu") return __gu.nav_home(inputs)
	if (locale === "he") return __he.nav_home(inputs)
	if (locale === "hi") return __hi.nav_home(inputs)
	if (locale === "id") return __id.nav_home(inputs)
	if (locale === "ja") return __ja.nav_home(inputs)
	if (locale === "kn") return __kn.nav_home(inputs)
	if (locale === "ko") return __ko.nav_home(inputs)
	if (locale === "ku") return __ku.nav_home(inputs)
	if (locale === "ml") return __ml.nav_home(inputs)
	if (locale === "mr") return __mr.nav_home(inputs)
	if (locale === "ne") return __ne.nav_home(inputs)
	if (locale === "or") return __or.nav_home(inputs)
	if (locale === "pa") return __pa.nav_home(inputs)
	if (locale === "pt") return __pt.nav_home(inputs)
	if (locale === "ru") return __ru.nav_home(inputs)
	if (locale === "si") return __si.nav_home(inputs)
	if (locale === "ta") return __ta.nav_home(inputs)
	if (locale === "te") return __te.nav_home(inputs)
	if (locale === "th") return __th.nav_home(inputs)
	if (locale === "tr") return __tr.nav_home(inputs)
	if (locale === "ur") return __ur.nav_home(inputs)
	if (locale === "vi") return __vi.nav_home(inputs)
	return __zh_hans1.nav_home(inputs)
});
/**
* | output |
* | --- |
* | "Search" |
*
* @param {Nav_SearchInputs} inputs
* @param {{ locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }} options
* @returns {LocalizedString}
*/
export const nav_search = /** @type {((inputs?: Nav_SearchInputs, options?: { locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }) => LocalizedString) & import('../runtime.js').MessageMetadata<Nav_SearchInputs, { locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }, {}>} */ ((inputs = {}, options = {}) => {
	const locale = experimentalStaticLocale ?? options.locale ?? getLocale()
	if (locale === "en") return __en.nav_search(inputs)
	if (locale === "ar") return __ar.nav_search(inputs)
	if (locale === "as") return __as.nav_search(inputs)
	if (locale === "bn") return __bn.nav_search(inputs)
	if (locale === "de") return __de.nav_search(inputs)
	if (locale === "es") return __es.nav_search(inputs)
	if (locale === "fa") return __fa.nav_search(inputs)
	if (locale === "fr") return __fr.nav_search(inputs)
	if (locale === "gu") return __gu.nav_search(inputs)
	if (locale === "he") return __he.nav_search(inputs)
	if (locale === "hi") return __hi.nav_search(inputs)
	if (locale === "id") return __id.nav_search(inputs)
	if (locale === "ja") return __ja.nav_search(inputs)
	if (locale === "kn") return __kn.nav_search(inputs)
	if (locale === "ko") return __ko.nav_search(inputs)
	if (locale === "ku") return __ku.nav_search(inputs)
	if (locale === "ml") return __ml.nav_search(inputs)
	if (locale === "mr") return __mr.nav_search(inputs)
	if (locale === "ne") return __ne.nav_search(inputs)
	if (locale === "or") return __or.nav_search(inputs)
	if (locale === "pa") return __pa.nav_search(inputs)
	if (locale === "pt") return __pt.nav_search(inputs)
	if (locale === "ru") return __ru.nav_search(inputs)
	if (locale === "si") return __si.nav_search(inputs)
	if (locale === "ta") return __ta.nav_search(inputs)
	if (locale === "te") return __te.nav_search(inputs)
	if (locale === "th") return __th.nav_search(inputs)
	if (locale === "tr") return __tr.nav_search(inputs)
	if (locale === "ur") return __ur.nav_search(inputs)
	if (locale === "vi") return __vi.nav_search(inputs)
	return __zh_hans1.nav_search(inputs)
});
/**
* | output |
* | --- |
* | "Messages" |
*
* @param {Nav_MessagesInputs} inputs
* @param {{ locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }} options
* @returns {LocalizedString}
*/
export const nav_messages = /** @type {((inputs?: Nav_MessagesInputs, options?: { locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }) => LocalizedString) & import('../runtime.js').MessageMetadata<Nav_MessagesInputs, { locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }, {}>} */ ((inputs = {}, options = {}) => {
	const locale = experimentalStaticLocale ?? options.locale ?? getLocale()
	if (locale === "en") return __en.nav_messages(inputs)
	if (locale === "ar") return __ar.nav_messages(inputs)
	if (locale === "as") return __as.nav_messages(inputs)
	if (locale === "bn") return __bn.nav_messages(inputs)
	if (locale === "de") return __de.nav_messages(inputs)
	if (locale === "es") return __es.nav_messages(inputs)
	if (locale === "fa") return __fa.nav_messages(inputs)
	if (locale === "fr") return __fr.nav_messages(inputs)
	if (locale === "gu") return __gu.nav_messages(inputs)
	if (locale === "he") return __he.nav_messages(inputs)
	if (locale === "hi") return __hi.nav_messages(inputs)
	if (locale === "id") return __id.nav_messages(inputs)
	if (locale === "ja") return __ja.nav_messages(inputs)
	if (locale === "kn") return __kn.nav_messages(inputs)
	if (locale === "ko") return __ko.nav_messages(inputs)
	if (locale === "ku") return __ku.nav_messages(inputs)
	if (locale === "ml") return __ml.nav_messages(inputs)
	if (locale === "mr") return __mr.nav_messages(inputs)
	if (locale === "ne") return __ne.nav_messages(inputs)
	if (locale === "or") return __or.nav_messages(inputs)
	if (locale === "pa") return __pa.nav_messages(inputs)
	if (locale === "pt") return __pt.nav_messages(inputs)
	if (locale === "ru") return __ru.nav_messages(inputs)
	if (locale === "si") return __si.nav_messages(inputs)
	if (locale === "ta") return __ta.nav_messages(inputs)
	if (locale === "te") return __te.nav_messages(inputs)
	if (locale === "th") return __th.nav_messages(inputs)
	if (locale === "tr") return __tr.nav_messages(inputs)
	if (locale === "ur") return __ur.nav_messages(inputs)
	if (locale === "vi") return __vi.nav_messages(inputs)
	return __zh_hans1.nav_messages(inputs)
});
/**
* | output |
* | --- |
* | "Apps" |
*
* @param {Nav_AppsInputs} inputs
* @param {{ locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }} options
* @returns {LocalizedString}
*/
export const nav_apps = /** @type {((inputs?: Nav_AppsInputs, options?: { locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }) => LocalizedString) & import('../runtime.js').MessageMetadata<Nav_AppsInputs, { locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }, {}>} */ ((inputs = {}, options = {}) => {
	const locale = experimentalStaticLocale ?? options.locale ?? getLocale()
	if (locale === "en") return __en.nav_apps(inputs)
	if (locale === "ar") return __ar.nav_apps(inputs)
	if (locale === "as") return __as.nav_apps(inputs)
	if (locale === "bn") return __bn.nav_apps(inputs)
	if (locale === "de") return __de.nav_apps(inputs)
	if (locale === "es") return __es.nav_apps(inputs)
	if (locale === "fa") return __fa.nav_apps(inputs)
	if (locale === "fr") return __fr.nav_apps(inputs)
	if (locale === "gu") return __gu.nav_apps(inputs)
	if (locale === "he") return __he.nav_apps(inputs)
	if (locale === "hi") return __hi.nav_apps(inputs)
	if (locale === "id") return __id.nav_apps(inputs)
	if (locale === "ja") return __ja.nav_apps(inputs)
	if (locale === "kn") return __kn.nav_apps(inputs)
	if (locale === "ko") return __ko.nav_apps(inputs)
	if (locale === "ku") return __ku.nav_apps(inputs)
	if (locale === "ml") return __ml.nav_apps(inputs)
	if (locale === "mr") return __mr.nav_apps(inputs)
	if (locale === "ne") return __ne.nav_apps(inputs)
	if (locale === "or") return __or.nav_apps(inputs)
	if (locale === "pa") return __pa.nav_apps(inputs)
	if (locale === "pt") return __pt.nav_apps(inputs)
	if (locale === "ru") return __ru.nav_apps(inputs)
	if (locale === "si") return __si.nav_apps(inputs)
	if (locale === "ta") return __ta.nav_apps(inputs)
	if (locale === "te") return __te.nav_apps(inputs)
	if (locale === "th") return __th.nav_apps(inputs)
	if (locale === "tr") return __tr.nav_apps(inputs)
	if (locale === "ur") return __ur.nav_apps(inputs)
	if (locale === "vi") return __vi.nav_apps(inputs)
	return __zh_hans1.nav_apps(inputs)
});
/**
* | output |
* | --- |
* | "Profile" |
*
* @param {Nav_ProfileInputs} inputs
* @param {{ locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }} options
* @returns {LocalizedString}
*/
export const nav_profile = /** @type {((inputs?: Nav_ProfileInputs, options?: { locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }) => LocalizedString) & import('../runtime.js').MessageMetadata<Nav_ProfileInputs, { locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }, {}>} */ ((inputs = {}, options = {}) => {
	const locale = experimentalStaticLocale ?? options.locale ?? getLocale()
	if (locale === "en") return __en.nav_profile(inputs)
	if (locale === "ar") return __ar.nav_profile(inputs)
	if (locale === "as") return __as.nav_profile(inputs)
	if (locale === "bn") return __bn.nav_profile(inputs)
	if (locale === "de") return __de.nav_profile(inputs)
	if (locale === "es") return __es.nav_profile(inputs)
	if (locale === "fa") return __fa.nav_profile(inputs)
	if (locale === "fr") return __fr.nav_profile(inputs)
	if (locale === "gu") return __gu.nav_profile(inputs)
	if (locale === "he") return __he.nav_profile(inputs)
	if (locale === "hi") return __hi.nav_profile(inputs)
	if (locale === "id") return __id.nav_profile(inputs)
	if (locale === "ja") return __ja.nav_profile(inputs)
	if (locale === "kn") return __kn.nav_profile(inputs)
	if (locale === "ko") return __ko.nav_profile(inputs)
	if (locale === "ku") return __ku.nav_profile(inputs)
	if (locale === "ml") return __ml.nav_profile(inputs)
	if (locale === "mr") return __mr.nav_profile(inputs)
	if (locale === "ne") return __ne.nav_profile(inputs)
	if (locale === "or") return __or.nav_profile(inputs)
	if (locale === "pa") return __pa.nav_profile(inputs)
	if (locale === "pt") return __pt.nav_profile(inputs)
	if (locale === "ru") return __ru.nav_profile(inputs)
	if (locale === "si") return __si.nav_profile(inputs)
	if (locale === "ta") return __ta.nav_profile(inputs)
	if (locale === "te") return __te.nav_profile(inputs)
	if (locale === "th") return __th.nav_profile(inputs)
	if (locale === "tr") return __tr.nav_profile(inputs)
	if (locale === "ur") return __ur.nav_profile(inputs)
	if (locale === "vi") return __vi.nav_profile(inputs)
	return __zh_hans1.nav_profile(inputs)
});
/**
* | output |
* | --- |
* | "Credits" |
*
* @param {Drawer_CreditsInputs} inputs
* @param {{ locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }} options
* @returns {LocalizedString}
*/
export const drawer_credits = /** @type {((inputs?: Drawer_CreditsInputs, options?: { locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }) => LocalizedString) & import('../runtime.js').MessageMetadata<Drawer_CreditsInputs, { locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }, {}>} */ ((inputs = {}, options = {}) => {
	const locale = experimentalStaticLocale ?? options.locale ?? getLocale()
	if (locale === "en") return __en.drawer_credits(inputs)
	if (locale === "ar") return __ar.drawer_credits(inputs)
	if (locale === "as") return __as.drawer_credits(inputs)
	if (locale === "bn") return __bn.drawer_credits(inputs)
	if (locale === "de") return __de.drawer_credits(inputs)
	if (locale === "es") return __es.drawer_credits(inputs)
	if (locale === "fa") return __fa.drawer_credits(inputs)
	if (locale === "fr") return __fr.drawer_credits(inputs)
	if (locale === "gu") return __gu.drawer_credits(inputs)
	if (locale === "he") return __he.drawer_credits(inputs)
	if (locale === "hi") return __hi.drawer_credits(inputs)
	if (locale === "id") return __id.drawer_credits(inputs)
	if (locale === "ja") return __ja.drawer_credits(inputs)
	if (locale === "kn") return __kn.drawer_credits(inputs)
	if (locale === "ko") return __ko.drawer_credits(inputs)
	if (locale === "ku") return __ku.drawer_credits(inputs)
	if (locale === "ml") return __ml.drawer_credits(inputs)
	if (locale === "mr") return __mr.drawer_credits(inputs)
	if (locale === "ne") return __ne.drawer_credits(inputs)
	if (locale === "or") return __or.drawer_credits(inputs)
	if (locale === "pa") return __pa.drawer_credits(inputs)
	if (locale === "pt") return __pt.drawer_credits(inputs)
	if (locale === "ru") return __ru.drawer_credits(inputs)
	if (locale === "si") return __si.drawer_credits(inputs)
	if (locale === "ta") return __ta.drawer_credits(inputs)
	if (locale === "te") return __te.drawer_credits(inputs)
	if (locale === "th") return __th.drawer_credits(inputs)
	if (locale === "tr") return __tr.drawer_credits(inputs)
	if (locale === "ur") return __ur.drawer_credits(inputs)
	if (locale === "vi") return __vi.drawer_credits(inputs)
	return __zh_hans1.drawer_credits(inputs)
});
/**
* | output |
* | --- |
* | "Murakumo" |
*
* @param {Drawer_MurakumoInputs} inputs
* @param {{ locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }} options
* @returns {LocalizedString}
*/
export const drawer_murakumo = /** @type {((inputs?: Drawer_MurakumoInputs, options?: { locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }) => LocalizedString) & import('../runtime.js').MessageMetadata<Drawer_MurakumoInputs, { locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }, {}>} */ ((inputs = {}, options = {}) => {
	const locale = experimentalStaticLocale ?? options.locale ?? getLocale()
	if (locale === "en") return __en.drawer_murakumo(inputs)
	if (locale === "ar") return __ar.drawer_murakumo(inputs)
	if (locale === "as") return __as.drawer_murakumo(inputs)
	if (locale === "bn") return __bn.drawer_murakumo(inputs)
	if (locale === "de") return __de.drawer_murakumo(inputs)
	if (locale === "es") return __es.drawer_murakumo(inputs)
	if (locale === "fa") return __fa.drawer_murakumo(inputs)
	if (locale === "fr") return __fr.drawer_murakumo(inputs)
	if (locale === "gu") return __gu.drawer_murakumo(inputs)
	if (locale === "he") return __he.drawer_murakumo(inputs)
	if (locale === "hi") return __hi.drawer_murakumo(inputs)
	if (locale === "id") return __id.drawer_murakumo(inputs)
	if (locale === "ja") return __ja.drawer_murakumo(inputs)
	if (locale === "kn") return __kn.drawer_murakumo(inputs)
	if (locale === "ko") return __ko.drawer_murakumo(inputs)
	if (locale === "ku") return __ku.drawer_murakumo(inputs)
	if (locale === "ml") return __ml.drawer_murakumo(inputs)
	if (locale === "mr") return __mr.drawer_murakumo(inputs)
	if (locale === "ne") return __ne.drawer_murakumo(inputs)
	if (locale === "or") return __or.drawer_murakumo(inputs)
	if (locale === "pa") return __pa.drawer_murakumo(inputs)
	if (locale === "pt") return __pt.drawer_murakumo(inputs)
	if (locale === "ru") return __ru.drawer_murakumo(inputs)
	if (locale === "si") return __si.drawer_murakumo(inputs)
	if (locale === "ta") return __ta.drawer_murakumo(inputs)
	if (locale === "te") return __te.drawer_murakumo(inputs)
	if (locale === "th") return __th.drawer_murakumo(inputs)
	if (locale === "tr") return __tr.drawer_murakumo(inputs)
	if (locale === "ur") return __ur.drawer_murakumo(inputs)
	if (locale === "vi") return __vi.drawer_murakumo(inputs)
	return __zh_hans1.drawer_murakumo(inputs)
});
/**
* | output |
* | --- |
* | "HC Tasks" |
*
* @param {Drawer_Hc_TasksInputs} inputs
* @param {{ locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }} options
* @returns {LocalizedString}
*/
export const drawer_hc_tasks = /** @type {((inputs?: Drawer_Hc_TasksInputs, options?: { locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }) => LocalizedString) & import('../runtime.js').MessageMetadata<Drawer_Hc_TasksInputs, { locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }, {}>} */ ((inputs = {}, options = {}) => {
	const locale = experimentalStaticLocale ?? options.locale ?? getLocale()
	if (locale === "en") return __en.drawer_hc_tasks(inputs)
	if (locale === "ar") return __ar.drawer_hc_tasks(inputs)
	if (locale === "as") return __as.drawer_hc_tasks(inputs)
	if (locale === "bn") return __bn.drawer_hc_tasks(inputs)
	if (locale === "de") return __de.drawer_hc_tasks(inputs)
	if (locale === "es") return __es.drawer_hc_tasks(inputs)
	if (locale === "fa") return __fa.drawer_hc_tasks(inputs)
	if (locale === "fr") return __fr.drawer_hc_tasks(inputs)
	if (locale === "gu") return __gu.drawer_hc_tasks(inputs)
	if (locale === "he") return __he.drawer_hc_tasks(inputs)
	if (locale === "hi") return __hi.drawer_hc_tasks(inputs)
	if (locale === "id") return __id.drawer_hc_tasks(inputs)
	if (locale === "ja") return __ja.drawer_hc_tasks(inputs)
	if (locale === "kn") return __kn.drawer_hc_tasks(inputs)
	if (locale === "ko") return __ko.drawer_hc_tasks(inputs)
	if (locale === "ku") return __ku.drawer_hc_tasks(inputs)
	if (locale === "ml") return __ml.drawer_hc_tasks(inputs)
	if (locale === "mr") return __mr.drawer_hc_tasks(inputs)
	if (locale === "ne") return __ne.drawer_hc_tasks(inputs)
	if (locale === "or") return __or.drawer_hc_tasks(inputs)
	if (locale === "pa") return __pa.drawer_hc_tasks(inputs)
	if (locale === "pt") return __pt.drawer_hc_tasks(inputs)
	if (locale === "ru") return __ru.drawer_hc_tasks(inputs)
	if (locale === "si") return __si.drawer_hc_tasks(inputs)
	if (locale === "ta") return __ta.drawer_hc_tasks(inputs)
	if (locale === "te") return __te.drawer_hc_tasks(inputs)
	if (locale === "th") return __th.drawer_hc_tasks(inputs)
	if (locale === "tr") return __tr.drawer_hc_tasks(inputs)
	if (locale === "ur") return __ur.drawer_hc_tasks(inputs)
	if (locale === "vi") return __vi.drawer_hc_tasks(inputs)
	return __zh_hans1.drawer_hc_tasks(inputs)
});
/**
* | output |
* | --- |
* | "Terms of Use" |
*
* @param {Drawer_TermsInputs} inputs
* @param {{ locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }} options
* @returns {LocalizedString}
*/
export const drawer_terms = /** @type {((inputs?: Drawer_TermsInputs, options?: { locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }) => LocalizedString) & import('../runtime.js').MessageMetadata<Drawer_TermsInputs, { locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }, {}>} */ ((inputs = {}, options = {}) => {
	const locale = experimentalStaticLocale ?? options.locale ?? getLocale()
	if (locale === "en") return __en.drawer_terms(inputs)
	if (locale === "ar") return __ar.drawer_terms(inputs)
	if (locale === "as") return __as.drawer_terms(inputs)
	if (locale === "bn") return __bn.drawer_terms(inputs)
	if (locale === "de") return __de.drawer_terms(inputs)
	if (locale === "es") return __es.drawer_terms(inputs)
	if (locale === "fa") return __fa.drawer_terms(inputs)
	if (locale === "fr") return __fr.drawer_terms(inputs)
	if (locale === "gu") return __gu.drawer_terms(inputs)
	if (locale === "he") return __he.drawer_terms(inputs)
	if (locale === "hi") return __hi.drawer_terms(inputs)
	if (locale === "id") return __id.drawer_terms(inputs)
	if (locale === "ja") return __ja.drawer_terms(inputs)
	if (locale === "kn") return __kn.drawer_terms(inputs)
	if (locale === "ko") return __ko.drawer_terms(inputs)
	if (locale === "ku") return __ku.drawer_terms(inputs)
	if (locale === "ml") return __ml.drawer_terms(inputs)
	if (locale === "mr") return __mr.drawer_terms(inputs)
	if (locale === "ne") return __ne.drawer_terms(inputs)
	if (locale === "or") return __or.drawer_terms(inputs)
	if (locale === "pa") return __pa.drawer_terms(inputs)
	if (locale === "pt") return __pt.drawer_terms(inputs)
	if (locale === "ru") return __ru.drawer_terms(inputs)
	if (locale === "si") return __si.drawer_terms(inputs)
	if (locale === "ta") return __ta.drawer_terms(inputs)
	if (locale === "te") return __te.drawer_terms(inputs)
	if (locale === "th") return __th.drawer_terms(inputs)
	if (locale === "tr") return __tr.drawer_terms(inputs)
	if (locale === "ur") return __ur.drawer_terms(inputs)
	if (locale === "vi") return __vi.drawer_terms(inputs)
	return __zh_hans1.drawer_terms(inputs)
});
/**
* | output |
* | --- |
* | "Privacy Policy" |
*
* @param {Drawer_PrivacyInputs} inputs
* @param {{ locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }} options
* @returns {LocalizedString}
*/
export const drawer_privacy = /** @type {((inputs?: Drawer_PrivacyInputs, options?: { locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }) => LocalizedString) & import('../runtime.js').MessageMetadata<Drawer_PrivacyInputs, { locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }, {}>} */ ((inputs = {}, options = {}) => {
	const locale = experimentalStaticLocale ?? options.locale ?? getLocale()
	if (locale === "en") return __en.drawer_privacy(inputs)
	if (locale === "ar") return __ar.drawer_privacy(inputs)
	if (locale === "as") return __as.drawer_privacy(inputs)
	if (locale === "bn") return __bn.drawer_privacy(inputs)
	if (locale === "de") return __de.drawer_privacy(inputs)
	if (locale === "es") return __es.drawer_privacy(inputs)
	if (locale === "fa") return __fa.drawer_privacy(inputs)
	if (locale === "fr") return __fr.drawer_privacy(inputs)
	if (locale === "gu") return __gu.drawer_privacy(inputs)
	if (locale === "he") return __he.drawer_privacy(inputs)
	if (locale === "hi") return __hi.drawer_privacy(inputs)
	if (locale === "id") return __id.drawer_privacy(inputs)
	if (locale === "ja") return __ja.drawer_privacy(inputs)
	if (locale === "kn") return __kn.drawer_privacy(inputs)
	if (locale === "ko") return __ko.drawer_privacy(inputs)
	if (locale === "ku") return __ku.drawer_privacy(inputs)
	if (locale === "ml") return __ml.drawer_privacy(inputs)
	if (locale === "mr") return __mr.drawer_privacy(inputs)
	if (locale === "ne") return __ne.drawer_privacy(inputs)
	if (locale === "or") return __or.drawer_privacy(inputs)
	if (locale === "pa") return __pa.drawer_privacy(inputs)
	if (locale === "pt") return __pt.drawer_privacy(inputs)
	if (locale === "ru") return __ru.drawer_privacy(inputs)
	if (locale === "si") return __si.drawer_privacy(inputs)
	if (locale === "ta") return __ta.drawer_privacy(inputs)
	if (locale === "te") return __te.drawer_privacy(inputs)
	if (locale === "th") return __th.drawer_privacy(inputs)
	if (locale === "tr") return __tr.drawer_privacy(inputs)
	if (locale === "ur") return __ur.drawer_privacy(inputs)
	if (locale === "vi") return __vi.drawer_privacy(inputs)
	return __zh_hans1.drawer_privacy(inputs)
});
/**
* | output |
* | --- |
* | "Feedback" |
*
* @param {Drawer_FeedbackInputs} inputs
* @param {{ locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }} options
* @returns {LocalizedString}
*/
export const drawer_feedback = /** @type {((inputs?: Drawer_FeedbackInputs, options?: { locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }) => LocalizedString) & import('../runtime.js').MessageMetadata<Drawer_FeedbackInputs, { locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }, {}>} */ ((inputs = {}, options = {}) => {
	const locale = experimentalStaticLocale ?? options.locale ?? getLocale()
	if (locale === "en") return __en.drawer_feedback(inputs)
	if (locale === "ar") return __ar.drawer_feedback(inputs)
	if (locale === "as") return __as.drawer_feedback(inputs)
	if (locale === "bn") return __bn.drawer_feedback(inputs)
	if (locale === "de") return __de.drawer_feedback(inputs)
	if (locale === "es") return __es.drawer_feedback(inputs)
	if (locale === "fa") return __fa.drawer_feedback(inputs)
	if (locale === "fr") return __fr.drawer_feedback(inputs)
	if (locale === "gu") return __gu.drawer_feedback(inputs)
	if (locale === "he") return __he.drawer_feedback(inputs)
	if (locale === "hi") return __hi.drawer_feedback(inputs)
	if (locale === "id") return __id.drawer_feedback(inputs)
	if (locale === "ja") return __ja.drawer_feedback(inputs)
	if (locale === "kn") return __kn.drawer_feedback(inputs)
	if (locale === "ko") return __ko.drawer_feedback(inputs)
	if (locale === "ku") return __ku.drawer_feedback(inputs)
	if (locale === "ml") return __ml.drawer_feedback(inputs)
	if (locale === "mr") return __mr.drawer_feedback(inputs)
	if (locale === "ne") return __ne.drawer_feedback(inputs)
	if (locale === "or") return __or.drawer_feedback(inputs)
	if (locale === "pa") return __pa.drawer_feedback(inputs)
	if (locale === "pt") return __pt.drawer_feedback(inputs)
	if (locale === "ru") return __ru.drawer_feedback(inputs)
	if (locale === "si") return __si.drawer_feedback(inputs)
	if (locale === "ta") return __ta.drawer_feedback(inputs)
	if (locale === "te") return __te.drawer_feedback(inputs)
	if (locale === "th") return __th.drawer_feedback(inputs)
	if (locale === "tr") return __tr.drawer_feedback(inputs)
	if (locale === "ur") return __ur.drawer_feedback(inputs)
	if (locale === "vi") return __vi.drawer_feedback(inputs)
	return __zh_hans1.drawer_feedback(inputs)
});
/**
* | output |
* | --- |
* | "Help" |
*
* @param {Drawer_HelpInputs} inputs
* @param {{ locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }} options
* @returns {LocalizedString}
*/
export const drawer_help = /** @type {((inputs?: Drawer_HelpInputs, options?: { locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }) => LocalizedString) & import('../runtime.js').MessageMetadata<Drawer_HelpInputs, { locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }, {}>} */ ((inputs = {}, options = {}) => {
	const locale = experimentalStaticLocale ?? options.locale ?? getLocale()
	if (locale === "en") return __en.drawer_help(inputs)
	if (locale === "ar") return __ar.drawer_help(inputs)
	if (locale === "as") return __as.drawer_help(inputs)
	if (locale === "bn") return __bn.drawer_help(inputs)
	if (locale === "de") return __de.drawer_help(inputs)
	if (locale === "es") return __es.drawer_help(inputs)
	if (locale === "fa") return __fa.drawer_help(inputs)
	if (locale === "fr") return __fr.drawer_help(inputs)
	if (locale === "gu") return __gu.drawer_help(inputs)
	if (locale === "he") return __he.drawer_help(inputs)
	if (locale === "hi") return __hi.drawer_help(inputs)
	if (locale === "id") return __id.drawer_help(inputs)
	if (locale === "ja") return __ja.drawer_help(inputs)
	if (locale === "kn") return __kn.drawer_help(inputs)
	if (locale === "ko") return __ko.drawer_help(inputs)
	if (locale === "ku") return __ku.drawer_help(inputs)
	if (locale === "ml") return __ml.drawer_help(inputs)
	if (locale === "mr") return __mr.drawer_help(inputs)
	if (locale === "ne") return __ne.drawer_help(inputs)
	if (locale === "or") return __or.drawer_help(inputs)
	if (locale === "pa") return __pa.drawer_help(inputs)
	if (locale === "pt") return __pt.drawer_help(inputs)
	if (locale === "ru") return __ru.drawer_help(inputs)
	if (locale === "si") return __si.drawer_help(inputs)
	if (locale === "ta") return __ta.drawer_help(inputs)
	if (locale === "te") return __te.drawer_help(inputs)
	if (locale === "th") return __th.drawer_help(inputs)
	if (locale === "tr") return __tr.drawer_help(inputs)
	if (locale === "ur") return __ur.drawer_help(inputs)
	if (locale === "vi") return __vi.drawer_help(inputs)
	return __zh_hans1.drawer_help(inputs)
});
/**
* | output |
* | --- |
* | "Browsing History" |
*
* @param {Drawer_HistoryInputs} inputs
* @param {{ locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }} options
* @returns {LocalizedString}
*/
export const drawer_history = /** @type {((inputs?: Drawer_HistoryInputs, options?: { locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }) => LocalizedString) & import('../runtime.js').MessageMetadata<Drawer_HistoryInputs, { locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }, {}>} */ ((inputs = {}, options = {}) => {
	const locale = experimentalStaticLocale ?? options.locale ?? getLocale()
	if (locale === "en") return __en.drawer_history(inputs)
	if (locale === "ar") return __ar.drawer_history(inputs)
	if (locale === "as") return __as.drawer_history(inputs)
	if (locale === "bn") return __bn.drawer_history(inputs)
	if (locale === "de") return __de.drawer_history(inputs)
	if (locale === "es") return __es.drawer_history(inputs)
	if (locale === "fa") return __fa.drawer_history(inputs)
	if (locale === "fr") return __fr.drawer_history(inputs)
	if (locale === "gu") return __gu.drawer_history(inputs)
	if (locale === "he") return __he.drawer_history(inputs)
	if (locale === "hi") return __hi.drawer_history(inputs)
	if (locale === "id") return __id.drawer_history(inputs)
	if (locale === "ja") return __ja.drawer_history(inputs)
	if (locale === "kn") return __kn.drawer_history(inputs)
	if (locale === "ko") return __ko.drawer_history(inputs)
	if (locale === "ku") return __ku.drawer_history(inputs)
	if (locale === "ml") return __ml.drawer_history(inputs)
	if (locale === "mr") return __mr.drawer_history(inputs)
	if (locale === "ne") return __ne.drawer_history(inputs)
	if (locale === "or") return __or.drawer_history(inputs)
	if (locale === "pa") return __pa.drawer_history(inputs)
	if (locale === "pt") return __pt.drawer_history(inputs)
	if (locale === "ru") return __ru.drawer_history(inputs)
	if (locale === "si") return __si.drawer_history(inputs)
	if (locale === "ta") return __ta.drawer_history(inputs)
	if (locale === "te") return __te.drawer_history(inputs)
	if (locale === "th") return __th.drawer_history(inputs)
	if (locale === "tr") return __tr.drawer_history(inputs)
	if (locale === "ur") return __ur.drawer_history(inputs)
	if (locale === "vi") return __vi.drawer_history(inputs)
	return __zh_hans1.drawer_history(inputs)
});
/**
* | output |
* | --- |
* | "Settings" |
*
* @param {Drawer_SettingsInputs} inputs
* @param {{ locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }} options
* @returns {LocalizedString}
*/
export const drawer_settings = /** @type {((inputs?: Drawer_SettingsInputs, options?: { locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }) => LocalizedString) & import('../runtime.js').MessageMetadata<Drawer_SettingsInputs, { locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }, {}>} */ ((inputs = {}, options = {}) => {
	const locale = experimentalStaticLocale ?? options.locale ?? getLocale()
	if (locale === "en") return __en.drawer_settings(inputs)
	if (locale === "ar") return __ar.drawer_settings(inputs)
	if (locale === "as") return __as.drawer_settings(inputs)
	if (locale === "bn") return __bn.drawer_settings(inputs)
	if (locale === "de") return __de.drawer_settings(inputs)
	if (locale === "es") return __es.drawer_settings(inputs)
	if (locale === "fa") return __fa.drawer_settings(inputs)
	if (locale === "fr") return __fr.drawer_settings(inputs)
	if (locale === "gu") return __gu.drawer_settings(inputs)
	if (locale === "he") return __he.drawer_settings(inputs)
	if (locale === "hi") return __hi.drawer_settings(inputs)
	if (locale === "id") return __id.drawer_settings(inputs)
	if (locale === "ja") return __ja.drawer_settings(inputs)
	if (locale === "kn") return __kn.drawer_settings(inputs)
	if (locale === "ko") return __ko.drawer_settings(inputs)
	if (locale === "ku") return __ku.drawer_settings(inputs)
	if (locale === "ml") return __ml.drawer_settings(inputs)
	if (locale === "mr") return __mr.drawer_settings(inputs)
	if (locale === "ne") return __ne.drawer_settings(inputs)
	if (locale === "or") return __or.drawer_settings(inputs)
	if (locale === "pa") return __pa.drawer_settings(inputs)
	if (locale === "pt") return __pt.drawer_settings(inputs)
	if (locale === "ru") return __ru.drawer_settings(inputs)
	if (locale === "si") return __si.drawer_settings(inputs)
	if (locale === "ta") return __ta.drawer_settings(inputs)
	if (locale === "te") return __te.drawer_settings(inputs)
	if (locale === "th") return __th.drawer_settings(inputs)
	if (locale === "tr") return __tr.drawer_settings(inputs)
	if (locale === "ur") return __ur.drawer_settings(inputs)
	if (locale === "vi") return __vi.drawer_settings(inputs)
	return __zh_hans1.drawer_settings(inputs)
});
/**
* | output |
* | --- |
* | "Sign Out" |
*
* @param {Drawer_Sign_OutInputs} inputs
* @param {{ locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }} options
* @returns {LocalizedString}
*/
export const drawer_sign_out = /** @type {((inputs?: Drawer_Sign_OutInputs, options?: { locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }) => LocalizedString) & import('../runtime.js').MessageMetadata<Drawer_Sign_OutInputs, { locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }, {}>} */ ((inputs = {}, options = {}) => {
	const locale = experimentalStaticLocale ?? options.locale ?? getLocale()
	if (locale === "en") return __en.drawer_sign_out(inputs)
	if (locale === "ar") return __ar.drawer_sign_out(inputs)
	if (locale === "as") return __as.drawer_sign_out(inputs)
	if (locale === "bn") return __bn.drawer_sign_out(inputs)
	if (locale === "de") return __de.drawer_sign_out(inputs)
	if (locale === "es") return __es.drawer_sign_out(inputs)
	if (locale === "fa") return __fa.drawer_sign_out(inputs)
	if (locale === "fr") return __fr.drawer_sign_out(inputs)
	if (locale === "gu") return __gu.drawer_sign_out(inputs)
	if (locale === "he") return __he.drawer_sign_out(inputs)
	if (locale === "hi") return __hi.drawer_sign_out(inputs)
	if (locale === "id") return __id.drawer_sign_out(inputs)
	if (locale === "ja") return __ja.drawer_sign_out(inputs)
	if (locale === "kn") return __kn.drawer_sign_out(inputs)
	if (locale === "ko") return __ko.drawer_sign_out(inputs)
	if (locale === "ku") return __ku.drawer_sign_out(inputs)
	if (locale === "ml") return __ml.drawer_sign_out(inputs)
	if (locale === "mr") return __mr.drawer_sign_out(inputs)
	if (locale === "ne") return __ne.drawer_sign_out(inputs)
	if (locale === "or") return __or.drawer_sign_out(inputs)
	if (locale === "pa") return __pa.drawer_sign_out(inputs)
	if (locale === "pt") return __pt.drawer_sign_out(inputs)
	if (locale === "ru") return __ru.drawer_sign_out(inputs)
	if (locale === "si") return __si.drawer_sign_out(inputs)
	if (locale === "ta") return __ta.drawer_sign_out(inputs)
	if (locale === "te") return __te.drawer_sign_out(inputs)
	if (locale === "th") return __th.drawer_sign_out(inputs)
	if (locale === "tr") return __tr.drawer_sign_out(inputs)
	if (locale === "ur") return __ur.drawer_sign_out(inputs)
	if (locale === "vi") return __vi.drawer_sign_out(inputs)
	return __zh_hans1.drawer_sign_out(inputs)
});
/**
* | output |
* | --- |
* | "Cookies" |
*
* @param {Cookie_TitleInputs} inputs
* @param {{ locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }} options
* @returns {LocalizedString}
*/
export const cookie_title = /** @type {((inputs?: Cookie_TitleInputs, options?: { locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }) => LocalizedString) & import('../runtime.js').MessageMetadata<Cookie_TitleInputs, { locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }, {}>} */ ((inputs = {}, options = {}) => {
	const locale = experimentalStaticLocale ?? options.locale ?? getLocale()
	if (locale === "en") return __en.cookie_title(inputs)
	if (locale === "ar") return __ar.cookie_title(inputs)
	if (locale === "as") return __as.cookie_title(inputs)
	if (locale === "bn") return __bn.cookie_title(inputs)
	if (locale === "de") return __de.cookie_title(inputs)
	if (locale === "es") return __es.cookie_title(inputs)
	if (locale === "fa") return __fa.cookie_title(inputs)
	if (locale === "fr") return __fr.cookie_title(inputs)
	if (locale === "gu") return __gu.cookie_title(inputs)
	if (locale === "he") return __he.cookie_title(inputs)
	if (locale === "hi") return __hi.cookie_title(inputs)
	if (locale === "id") return __id.cookie_title(inputs)
	if (locale === "ja") return __ja.cookie_title(inputs)
	if (locale === "kn") return __kn.cookie_title(inputs)
	if (locale === "ko") return __ko.cookie_title(inputs)
	if (locale === "ku") return __ku.cookie_title(inputs)
	if (locale === "ml") return __ml.cookie_title(inputs)
	if (locale === "mr") return __mr.cookie_title(inputs)
	if (locale === "ne") return __ne.cookie_title(inputs)
	if (locale === "or") return __or.cookie_title(inputs)
	if (locale === "pa") return __pa.cookie_title(inputs)
	if (locale === "pt") return __pt.cookie_title(inputs)
	if (locale === "ru") return __ru.cookie_title(inputs)
	if (locale === "si") return __si.cookie_title(inputs)
	if (locale === "ta") return __ta.cookie_title(inputs)
	if (locale === "te") return __te.cookie_title(inputs)
	if (locale === "th") return __th.cookie_title(inputs)
	if (locale === "tr") return __tr.cookie_title(inputs)
	if (locale === "ur") return __ur.cookie_title(inputs)
	if (locale === "vi") return __vi.cookie_title(inputs)
	return __zh_hans1.cookie_title(inputs)
});
/**
* | output |
* | --- |
* | "YORO uses cookies to serve relevant ads via Google AdSense and partner networks. See our Privacy Policy for details." |
*
* @param {Cookie_DescriptionInputs} inputs
* @param {{ locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }} options
* @returns {LocalizedString}
*/
export const cookie_description = /** @type {((inputs?: Cookie_DescriptionInputs, options?: { locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }) => LocalizedString) & import('../runtime.js').MessageMetadata<Cookie_DescriptionInputs, { locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }, {}>} */ ((inputs = {}, options = {}) => {
	const locale = experimentalStaticLocale ?? options.locale ?? getLocale()
	if (locale === "en") return __en.cookie_description(inputs)
	if (locale === "ar") return __ar.cookie_description(inputs)
	if (locale === "as") return __as.cookie_description(inputs)
	if (locale === "bn") return __bn.cookie_description(inputs)
	if (locale === "de") return __de.cookie_description(inputs)
	if (locale === "es") return __es.cookie_description(inputs)
	if (locale === "fa") return __fa.cookie_description(inputs)
	if (locale === "fr") return __fr.cookie_description(inputs)
	if (locale === "gu") return __gu.cookie_description(inputs)
	if (locale === "he") return __he.cookie_description(inputs)
	if (locale === "hi") return __hi.cookie_description(inputs)
	if (locale === "id") return __id.cookie_description(inputs)
	if (locale === "ja") return __ja.cookie_description(inputs)
	if (locale === "kn") return __kn.cookie_description(inputs)
	if (locale === "ko") return __ko.cookie_description(inputs)
	if (locale === "ku") return __ku.cookie_description(inputs)
	if (locale === "ml") return __ml.cookie_description(inputs)
	if (locale === "mr") return __mr.cookie_description(inputs)
	if (locale === "ne") return __ne.cookie_description(inputs)
	if (locale === "or") return __or.cookie_description(inputs)
	if (locale === "pa") return __pa.cookie_description(inputs)
	if (locale === "pt") return __pt.cookie_description(inputs)
	if (locale === "ru") return __ru.cookie_description(inputs)
	if (locale === "si") return __si.cookie_description(inputs)
	if (locale === "ta") return __ta.cookie_description(inputs)
	if (locale === "te") return __te.cookie_description(inputs)
	if (locale === "th") return __th.cookie_description(inputs)
	if (locale === "tr") return __tr.cookie_description(inputs)
	if (locale === "ur") return __ur.cookie_description(inputs)
	if (locale === "vi") return __vi.cookie_description(inputs)
	return __zh_hans1.cookie_description(inputs)
});
/**
* | output |
* | --- |
* | "Decline" |
*
* @param {Cookie_DeclineInputs} inputs
* @param {{ locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }} options
* @returns {LocalizedString}
*/
export const cookie_decline = /** @type {((inputs?: Cookie_DeclineInputs, options?: { locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }) => LocalizedString) & import('../runtime.js').MessageMetadata<Cookie_DeclineInputs, { locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }, {}>} */ ((inputs = {}, options = {}) => {
	const locale = experimentalStaticLocale ?? options.locale ?? getLocale()
	if (locale === "en") return __en.cookie_decline(inputs)
	if (locale === "ar") return __ar.cookie_decline(inputs)
	if (locale === "as") return __as.cookie_decline(inputs)
	if (locale === "bn") return __bn.cookie_decline(inputs)
	if (locale === "de") return __de.cookie_decline(inputs)
	if (locale === "es") return __es.cookie_decline(inputs)
	if (locale === "fa") return __fa.cookie_decline(inputs)
	if (locale === "fr") return __fr.cookie_decline(inputs)
	if (locale === "gu") return __gu.cookie_decline(inputs)
	if (locale === "he") return __he.cookie_decline(inputs)
	if (locale === "hi") return __hi.cookie_decline(inputs)
	if (locale === "id") return __id.cookie_decline(inputs)
	if (locale === "ja") return __ja.cookie_decline(inputs)
	if (locale === "kn") return __kn.cookie_decline(inputs)
	if (locale === "ko") return __ko.cookie_decline(inputs)
	if (locale === "ku") return __ku.cookie_decline(inputs)
	if (locale === "ml") return __ml.cookie_decline(inputs)
	if (locale === "mr") return __mr.cookie_decline(inputs)
	if (locale === "ne") return __ne.cookie_decline(inputs)
	if (locale === "or") return __or.cookie_decline(inputs)
	if (locale === "pa") return __pa.cookie_decline(inputs)
	if (locale === "pt") return __pt.cookie_decline(inputs)
	if (locale === "ru") return __ru.cookie_decline(inputs)
	if (locale === "si") return __si.cookie_decline(inputs)
	if (locale === "ta") return __ta.cookie_decline(inputs)
	if (locale === "te") return __te.cookie_decline(inputs)
	if (locale === "th") return __th.cookie_decline(inputs)
	if (locale === "tr") return __tr.cookie_decline(inputs)
	if (locale === "ur") return __ur.cookie_decline(inputs)
	if (locale === "vi") return __vi.cookie_decline(inputs)
	return __zh_hans1.cookie_decline(inputs)
});
/**
* | output |
* | --- |
* | "Accept" |
*
* @param {Cookie_AcceptInputs} inputs
* @param {{ locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }} options
* @returns {LocalizedString}
*/
export const cookie_accept = /** @type {((inputs?: Cookie_AcceptInputs, options?: { locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }) => LocalizedString) & import('../runtime.js').MessageMetadata<Cookie_AcceptInputs, { locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }, {}>} */ ((inputs = {}, options = {}) => {
	const locale = experimentalStaticLocale ?? options.locale ?? getLocale()
	if (locale === "en") return __en.cookie_accept(inputs)
	if (locale === "ar") return __ar.cookie_accept(inputs)
	if (locale === "as") return __as.cookie_accept(inputs)
	if (locale === "bn") return __bn.cookie_accept(inputs)
	if (locale === "de") return __de.cookie_accept(inputs)
	if (locale === "es") return __es.cookie_accept(inputs)
	if (locale === "fa") return __fa.cookie_accept(inputs)
	if (locale === "fr") return __fr.cookie_accept(inputs)
	if (locale === "gu") return __gu.cookie_accept(inputs)
	if (locale === "he") return __he.cookie_accept(inputs)
	if (locale === "hi") return __hi.cookie_accept(inputs)
	if (locale === "id") return __id.cookie_accept(inputs)
	if (locale === "ja") return __ja.cookie_accept(inputs)
	if (locale === "kn") return __kn.cookie_accept(inputs)
	if (locale === "ko") return __ko.cookie_accept(inputs)
	if (locale === "ku") return __ku.cookie_accept(inputs)
	if (locale === "ml") return __ml.cookie_accept(inputs)
	if (locale === "mr") return __mr.cookie_accept(inputs)
	if (locale === "ne") return __ne.cookie_accept(inputs)
	if (locale === "or") return __or.cookie_accept(inputs)
	if (locale === "pa") return __pa.cookie_accept(inputs)
	if (locale === "pt") return __pt.cookie_accept(inputs)
	if (locale === "ru") return __ru.cookie_accept(inputs)
	if (locale === "si") return __si.cookie_accept(inputs)
	if (locale === "ta") return __ta.cookie_accept(inputs)
	if (locale === "te") return __te.cookie_accept(inputs)
	if (locale === "th") return __th.cookie_accept(inputs)
	if (locale === "tr") return __tr.cookie_accept(inputs)
	if (locale === "ur") return __ur.cookie_accept(inputs)
	if (locale === "vi") return __vi.cookie_accept(inputs)
	return __zh_hans1.cookie_accept(inputs)
});
/**
* | output |
* | --- |
* | "Important Notice Regarding Inference Participation" |
*
* @param {Inference_Important_NoticeInputs} inputs
* @param {{ locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }} options
* @returns {LocalizedString}
*/
export const inference_important_notice = /** @type {((inputs?: Inference_Important_NoticeInputs, options?: { locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }) => LocalizedString) & import('../runtime.js').MessageMetadata<Inference_Important_NoticeInputs, { locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }, {}>} */ ((inputs = {}, options = {}) => {
	const locale = experimentalStaticLocale ?? options.locale ?? getLocale()
	if (locale === "en") return __en.inference_important_notice(inputs)
	if (locale === "ar") return __ar.inference_important_notice(inputs)
	if (locale === "as") return __as.inference_important_notice(inputs)
	if (locale === "bn") return __bn.inference_important_notice(inputs)
	if (locale === "de") return __de.inference_important_notice(inputs)
	if (locale === "es") return __es.inference_important_notice(inputs)
	if (locale === "fa") return __fa.inference_important_notice(inputs)
	if (locale === "fr") return __fr.inference_important_notice(inputs)
	if (locale === "gu") return __gu.inference_important_notice(inputs)
	if (locale === "he") return __he.inference_important_notice(inputs)
	if (locale === "hi") return __hi.inference_important_notice(inputs)
	if (locale === "id") return __id.inference_important_notice(inputs)
	if (locale === "ja") return __ja.inference_important_notice(inputs)
	if (locale === "kn") return __kn.inference_important_notice(inputs)
	if (locale === "ko") return __ko.inference_important_notice(inputs)
	if (locale === "ku") return __ku.inference_important_notice(inputs)
	if (locale === "ml") return __ml.inference_important_notice(inputs)
	if (locale === "mr") return __mr.inference_important_notice(inputs)
	if (locale === "ne") return __ne.inference_important_notice(inputs)
	if (locale === "or") return __or.inference_important_notice(inputs)
	if (locale === "pa") return __pa.inference_important_notice(inputs)
	if (locale === "pt") return __pt.inference_important_notice(inputs)
	if (locale === "ru") return __ru.inference_important_notice(inputs)
	if (locale === "si") return __si.inference_important_notice(inputs)
	if (locale === "ta") return __ta.inference_important_notice(inputs)
	if (locale === "te") return __te.inference_important_notice(inputs)
	if (locale === "th") return __th.inference_important_notice(inputs)
	if (locale === "tr") return __tr.inference_important_notice(inputs)
	if (locale === "ur") return __ur.inference_important_notice(inputs)
	if (locale === "vi") return __vi.inference_important_notice(inputs)
	return __zh_hans1.inference_important_notice(inputs)
});
/**
* | output |
* | --- |
* | "Please scroll to the bottom" |
*
* @param {Inference_Scroll_PromptInputs} inputs
* @param {{ locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }} options
* @returns {LocalizedString}
*/
export const inference_scroll_prompt = /** @type {((inputs?: Inference_Scroll_PromptInputs, options?: { locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }) => LocalizedString) & import('../runtime.js').MessageMetadata<Inference_Scroll_PromptInputs, { locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }, {}>} */ ((inputs = {}, options = {}) => {
	const locale = experimentalStaticLocale ?? options.locale ?? getLocale()
	if (locale === "en") return __en.inference_scroll_prompt(inputs)
	if (locale === "ar") return __ar.inference_scroll_prompt(inputs)
	if (locale === "as") return __as.inference_scroll_prompt(inputs)
	if (locale === "bn") return __bn.inference_scroll_prompt(inputs)
	if (locale === "de") return __de.inference_scroll_prompt(inputs)
	if (locale === "es") return __es.inference_scroll_prompt(inputs)
	if (locale === "fa") return __fa.inference_scroll_prompt(inputs)
	if (locale === "fr") return __fr.inference_scroll_prompt(inputs)
	if (locale === "gu") return __gu.inference_scroll_prompt(inputs)
	if (locale === "he") return __he.inference_scroll_prompt(inputs)
	if (locale === "hi") return __hi.inference_scroll_prompt(inputs)
	if (locale === "id") return __id.inference_scroll_prompt(inputs)
	if (locale === "ja") return __ja.inference_scroll_prompt(inputs)
	if (locale === "kn") return __kn.inference_scroll_prompt(inputs)
	if (locale === "ko") return __ko.inference_scroll_prompt(inputs)
	if (locale === "ku") return __ku.inference_scroll_prompt(inputs)
	if (locale === "ml") return __ml.inference_scroll_prompt(inputs)
	if (locale === "mr") return __mr.inference_scroll_prompt(inputs)
	if (locale === "ne") return __ne.inference_scroll_prompt(inputs)
	if (locale === "or") return __or.inference_scroll_prompt(inputs)
	if (locale === "pa") return __pa.inference_scroll_prompt(inputs)
	if (locale === "pt") return __pt.inference_scroll_prompt(inputs)
	if (locale === "ru") return __ru.inference_scroll_prompt(inputs)
	if (locale === "si") return __si.inference_scroll_prompt(inputs)
	if (locale === "ta") return __ta.inference_scroll_prompt(inputs)
	if (locale === "te") return __te.inference_scroll_prompt(inputs)
	if (locale === "th") return __th.inference_scroll_prompt(inputs)
	if (locale === "tr") return __tr.inference_scroll_prompt(inputs)
	if (locale === "ur") return __ur.inference_scroll_prompt(inputs)
	if (locale === "vi") return __vi.inference_scroll_prompt(inputs)
	return __zh_hans1.inference_scroll_prompt(inputs)
});
/**
* | output |
* | --- |
* | "I have read, understood, and agree to all provisions of the Browser Inference Participation Terms above, including device resource usage, disclaimers, and in..." |
*
* @param {Inference_Agree_CheckboxInputs} inputs
* @param {{ locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }} options
* @returns {LocalizedString}
*/
export const inference_agree_checkbox = /** @type {((inputs?: Inference_Agree_CheckboxInputs, options?: { locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }) => LocalizedString) & import('../runtime.js').MessageMetadata<Inference_Agree_CheckboxInputs, { locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }, {}>} */ ((inputs = {}, options = {}) => {
	const locale = experimentalStaticLocale ?? options.locale ?? getLocale()
	if (locale === "en") return __en.inference_agree_checkbox(inputs)
	if (locale === "ar") return __ar.inference_agree_checkbox(inputs)
	if (locale === "as") return __as.inference_agree_checkbox(inputs)
	if (locale === "bn") return __bn.inference_agree_checkbox(inputs)
	if (locale === "de") return __de.inference_agree_checkbox(inputs)
	if (locale === "es") return __es.inference_agree_checkbox(inputs)
	if (locale === "fa") return __fa.inference_agree_checkbox(inputs)
	if (locale === "fr") return __fr.inference_agree_checkbox(inputs)
	if (locale === "gu") return __gu.inference_agree_checkbox(inputs)
	if (locale === "he") return __he.inference_agree_checkbox(inputs)
	if (locale === "hi") return __hi.inference_agree_checkbox(inputs)
	if (locale === "id") return __id.inference_agree_checkbox(inputs)
	if (locale === "ja") return __ja.inference_agree_checkbox(inputs)
	if (locale === "kn") return __kn.inference_agree_checkbox(inputs)
	if (locale === "ko") return __ko.inference_agree_checkbox(inputs)
	if (locale === "ku") return __ku.inference_agree_checkbox(inputs)
	if (locale === "ml") return __ml.inference_agree_checkbox(inputs)
	if (locale === "mr") return __mr.inference_agree_checkbox(inputs)
	if (locale === "ne") return __ne.inference_agree_checkbox(inputs)
	if (locale === "or") return __or.inference_agree_checkbox(inputs)
	if (locale === "pa") return __pa.inference_agree_checkbox(inputs)
	if (locale === "pt") return __pt.inference_agree_checkbox(inputs)
	if (locale === "ru") return __ru.inference_agree_checkbox(inputs)
	if (locale === "si") return __si.inference_agree_checkbox(inputs)
	if (locale === "ta") return __ta.inference_agree_checkbox(inputs)
	if (locale === "te") return __te.inference_agree_checkbox(inputs)
	if (locale === "th") return __th.inference_agree_checkbox(inputs)
	if (locale === "tr") return __tr.inference_agree_checkbox(inputs)
	if (locale === "ur") return __ur.inference_agree_checkbox(inputs)
	if (locale === "vi") return __vi.inference_agree_checkbox(inputs)
	return __zh_hans1.inference_agree_checkbox(inputs)
});
/**
* | output |
* | --- |
* | "Decline" |
*
* @param {Inference_DeclineInputs} inputs
* @param {{ locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }} options
* @returns {LocalizedString}
*/
export const inference_decline = /** @type {((inputs?: Inference_DeclineInputs, options?: { locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }) => LocalizedString) & import('../runtime.js').MessageMetadata<Inference_DeclineInputs, { locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }, {}>} */ ((inputs = {}, options = {}) => {
	const locale = experimentalStaticLocale ?? options.locale ?? getLocale()
	if (locale === "en") return __en.inference_decline(inputs)
	if (locale === "ar") return __ar.inference_decline(inputs)
	if (locale === "as") return __as.inference_decline(inputs)
	if (locale === "bn") return __bn.inference_decline(inputs)
	if (locale === "de") return __de.inference_decline(inputs)
	if (locale === "es") return __es.inference_decline(inputs)
	if (locale === "fa") return __fa.inference_decline(inputs)
	if (locale === "fr") return __fr.inference_decline(inputs)
	if (locale === "gu") return __gu.inference_decline(inputs)
	if (locale === "he") return __he.inference_decline(inputs)
	if (locale === "hi") return __hi.inference_decline(inputs)
	if (locale === "id") return __id.inference_decline(inputs)
	if (locale === "ja") return __ja.inference_decline(inputs)
	if (locale === "kn") return __kn.inference_decline(inputs)
	if (locale === "ko") return __ko.inference_decline(inputs)
	if (locale === "ku") return __ku.inference_decline(inputs)
	if (locale === "ml") return __ml.inference_decline(inputs)
	if (locale === "mr") return __mr.inference_decline(inputs)
	if (locale === "ne") return __ne.inference_decline(inputs)
	if (locale === "or") return __or.inference_decline(inputs)
	if (locale === "pa") return __pa.inference_decline(inputs)
	if (locale === "pt") return __pt.inference_decline(inputs)
	if (locale === "ru") return __ru.inference_decline(inputs)
	if (locale === "si") return __si.inference_decline(inputs)
	if (locale === "ta") return __ta.inference_decline(inputs)
	if (locale === "te") return __te.inference_decline(inputs)
	if (locale === "th") return __th.inference_decline(inputs)
	if (locale === "tr") return __tr.inference_decline(inputs)
	if (locale === "ur") return __ur.inference_decline(inputs)
	if (locale === "vi") return __vi.inference_decline(inputs)
	return __zh_hans1.inference_decline(inputs)
});
/**
* | output |
* | --- |
* | "Agree and Join Inference" |
*
* @param {Inference_AgreeInputs} inputs
* @param {{ locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }} options
* @returns {LocalizedString}
*/
export const inference_agree = /** @type {((inputs?: Inference_AgreeInputs, options?: { locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }) => LocalizedString) & import('../runtime.js').MessageMetadata<Inference_AgreeInputs, { locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }, {}>} */ ((inputs = {}, options = {}) => {
	const locale = experimentalStaticLocale ?? options.locale ?? getLocale()
	if (locale === "en") return __en.inference_agree(inputs)
	if (locale === "ar") return __ar.inference_agree(inputs)
	if (locale === "as") return __as.inference_agree(inputs)
	if (locale === "bn") return __bn.inference_agree(inputs)
	if (locale === "de") return __de.inference_agree(inputs)
	if (locale === "es") return __es.inference_agree(inputs)
	if (locale === "fa") return __fa.inference_agree(inputs)
	if (locale === "fr") return __fr.inference_agree(inputs)
	if (locale === "gu") return __gu.inference_agree(inputs)
	if (locale === "he") return __he.inference_agree(inputs)
	if (locale === "hi") return __hi.inference_agree(inputs)
	if (locale === "id") return __id.inference_agree(inputs)
	if (locale === "ja") return __ja.inference_agree(inputs)
	if (locale === "kn") return __kn.inference_agree(inputs)
	if (locale === "ko") return __ko.inference_agree(inputs)
	if (locale === "ku") return __ku.inference_agree(inputs)
	if (locale === "ml") return __ml.inference_agree(inputs)
	if (locale === "mr") return __mr.inference_agree(inputs)
	if (locale === "ne") return __ne.inference_agree(inputs)
	if (locale === "or") return __or.inference_agree(inputs)
	if (locale === "pa") return __pa.inference_agree(inputs)
	if (locale === "pt") return __pt.inference_agree(inputs)
	if (locale === "ru") return __ru.inference_agree(inputs)
	if (locale === "si") return __si.inference_agree(inputs)
	if (locale === "ta") return __ta.inference_agree(inputs)
	if (locale === "te") return __te.inference_agree(inputs)
	if (locale === "th") return __th.inference_agree(inputs)
	if (locale === "tr") return __tr.inference_agree(inputs)
	if (locale === "ur") return __ur.inference_agree(inputs)
	if (locale === "vi") return __vi.inference_agree(inputs)
	return __zh_hans1.inference_agree(inputs)
});
/**
* | output |
* | --- |
* | "Back" |
*
* @param {Content_Label_BackInputs} inputs
* @param {{ locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }} options
* @returns {LocalizedString}
*/
export const content_label_back = /** @type {((inputs?: Content_Label_BackInputs, options?: { locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }) => LocalizedString) & import('../runtime.js').MessageMetadata<Content_Label_BackInputs, { locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }, {}>} */ ((inputs = {}, options = {}) => {
	const locale = experimentalStaticLocale ?? options.locale ?? getLocale()
	if (locale === "en") return __en.content_label_back(inputs)
	if (locale === "ar") return __ar.content_label_back(inputs)
	if (locale === "as") return __as.content_label_back(inputs)
	if (locale === "bn") return __bn.content_label_back(inputs)
	if (locale === "de") return __de.content_label_back(inputs)
	if (locale === "es") return __es.content_label_back(inputs)
	if (locale === "fa") return __fa.content_label_back(inputs)
	if (locale === "fr") return __fr.content_label_back(inputs)
	if (locale === "gu") return __gu.content_label_back(inputs)
	if (locale === "he") return __he.content_label_back(inputs)
	if (locale === "hi") return __hi.content_label_back(inputs)
	if (locale === "id") return __id.content_label_back(inputs)
	if (locale === "ja") return __ja.content_label_back(inputs)
	if (locale === "kn") return __kn.content_label_back(inputs)
	if (locale === "ko") return __ko.content_label_back(inputs)
	if (locale === "ku") return __ku.content_label_back(inputs)
	if (locale === "ml") return __ml.content_label_back(inputs)
	if (locale === "mr") return __mr.content_label_back(inputs)
	if (locale === "ne") return __ne.content_label_back(inputs)
	if (locale === "or") return __or.content_label_back(inputs)
	if (locale === "pa") return __pa.content_label_back(inputs)
	if (locale === "pt") return __pt.content_label_back(inputs)
	if (locale === "ru") return __ru.content_label_back(inputs)
	if (locale === "si") return __si.content_label_back(inputs)
	if (locale === "ta") return __ta.content_label_back(inputs)
	if (locale === "te") return __te.content_label_back(inputs)
	if (locale === "th") return __th.content_label_back(inputs)
	if (locale === "tr") return __tr.content_label_back(inputs)
	if (locale === "ur") return __ur.content_label_back(inputs)
	if (locale === "vi") return __vi.content_label_back(inputs)
	return __zh_hans1.content_label_back(inputs)
});
/**
* | output |
* | --- |
* | "I agree to the above" |
*
* @param {Content_Label_AgreeInputs} inputs
* @param {{ locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }} options
* @returns {LocalizedString}
*/
export const content_label_agree = /** @type {((inputs?: Content_Label_AgreeInputs, options?: { locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }) => LocalizedString) & import('../runtime.js').MessageMetadata<Content_Label_AgreeInputs, { locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }, {}>} */ ((inputs = {}, options = {}) => {
	const locale = experimentalStaticLocale ?? options.locale ?? getLocale()
	if (locale === "en") return __en.content_label_agree(inputs)
	if (locale === "ar") return __ar.content_label_agree(inputs)
	if (locale === "as") return __as.content_label_agree(inputs)
	if (locale === "bn") return __bn.content_label_agree(inputs)
	if (locale === "de") return __de.content_label_agree(inputs)
	if (locale === "es") return __es.content_label_agree(inputs)
	if (locale === "fa") return __fa.content_label_agree(inputs)
	if (locale === "fr") return __fr.content_label_agree(inputs)
	if (locale === "gu") return __gu.content_label_agree(inputs)
	if (locale === "he") return __he.content_label_agree(inputs)
	if (locale === "hi") return __hi.content_label_agree(inputs)
	if (locale === "id") return __id.content_label_agree(inputs)
	if (locale === "ja") return __ja.content_label_agree(inputs)
	if (locale === "kn") return __kn.content_label_agree(inputs)
	if (locale === "ko") return __ko.content_label_agree(inputs)
	if (locale === "ku") return __ku.content_label_agree(inputs)
	if (locale === "ml") return __ml.content_label_agree(inputs)
	if (locale === "mr") return __mr.content_label_agree(inputs)
	if (locale === "ne") return __ne.content_label_agree(inputs)
	if (locale === "or") return __or.content_label_agree(inputs)
	if (locale === "pa") return __pa.content_label_agree(inputs)
	if (locale === "pt") return __pt.content_label_agree(inputs)
	if (locale === "ru") return __ru.content_label_agree(inputs)
	if (locale === "si") return __si.content_label_agree(inputs)
	if (locale === "ta") return __ta.content_label_agree(inputs)
	if (locale === "te") return __te.content_label_agree(inputs)
	if (locale === "th") return __th.content_label_agree(inputs)
	if (locale === "tr") return __tr.content_label_agree(inputs)
	if (locale === "ur") return __ur.content_label_agree(inputs)
	if (locale === "vi") return __vi.content_label_agree(inputs)
	return __zh_hans1.content_label_agree(inputs)
});
/**
* | output |
* | --- |
* | "Spam Block" |
*
* @param {Profile_Spam_BlockInputs} inputs
* @param {{ locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }} options
* @returns {LocalizedString}
*/
export const profile_spam_block = /** @type {((inputs?: Profile_Spam_BlockInputs, options?: { locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }) => LocalizedString) & import('../runtime.js').MessageMetadata<Profile_Spam_BlockInputs, { locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }, {}>} */ ((inputs = {}, options = {}) => {
	const locale = experimentalStaticLocale ?? options.locale ?? getLocale()
	if (locale === "en") return __en.profile_spam_block(inputs)
	if (locale === "ar") return __ar.profile_spam_block(inputs)
	if (locale === "as") return __as.profile_spam_block(inputs)
	if (locale === "bn") return __bn.profile_spam_block(inputs)
	if (locale === "de") return __de.profile_spam_block(inputs)
	if (locale === "es") return __es.profile_spam_block(inputs)
	if (locale === "fa") return __fa.profile_spam_block(inputs)
	if (locale === "fr") return __fr.profile_spam_block(inputs)
	if (locale === "gu") return __gu.profile_spam_block(inputs)
	if (locale === "he") return __he.profile_spam_block(inputs)
	if (locale === "hi") return __hi.profile_spam_block(inputs)
	if (locale === "id") return __id.profile_spam_block(inputs)
	if (locale === "ja") return __ja.profile_spam_block(inputs)
	if (locale === "kn") return __kn.profile_spam_block(inputs)
	if (locale === "ko") return __ko.profile_spam_block(inputs)
	if (locale === "ku") return __ku.profile_spam_block(inputs)
	if (locale === "ml") return __ml.profile_spam_block(inputs)
	if (locale === "mr") return __mr.profile_spam_block(inputs)
	if (locale === "ne") return __ne.profile_spam_block(inputs)
	if (locale === "or") return __or.profile_spam_block(inputs)
	if (locale === "pa") return __pa.profile_spam_block(inputs)
	if (locale === "pt") return __pt.profile_spam_block(inputs)
	if (locale === "ru") return __ru.profile_spam_block(inputs)
	if (locale === "si") return __si.profile_spam_block(inputs)
	if (locale === "ta") return __ta.profile_spam_block(inputs)
	if (locale === "te") return __te.profile_spam_block(inputs)
	if (locale === "th") return __th.profile_spam_block(inputs)
	if (locale === "tr") return __tr.profile_spam_block(inputs)
	if (locale === "ur") return __ur.profile_spam_block(inputs)
	if (locale === "vi") return __vi.profile_spam_block(inputs)
	return __zh_hans1.profile_spam_block(inputs)
});
/**
* | output |
* | --- |
* | "Auto-reject Trust Score below {threshold}" |
*
* @param {Profile_Spam_Block_DescInputs} inputs
* @param {{ locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }} options
* @returns {LocalizedString}
*/
export const profile_spam_block_desc = /** @type {((inputs: Profile_Spam_Block_DescInputs, options?: { locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }) => LocalizedString) & import('../runtime.js').MessageMetadata<Profile_Spam_Block_DescInputs, { locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }, {}>} */ ((inputs, options = {}) => {
	const locale = experimentalStaticLocale ?? options.locale ?? getLocale()
	if (locale === "en") return __en.profile_spam_block_desc(inputs)
	if (locale === "ar") return __ar.profile_spam_block_desc(inputs)
	if (locale === "as") return __as.profile_spam_block_desc(inputs)
	if (locale === "bn") return __bn.profile_spam_block_desc(inputs)
	if (locale === "de") return __de.profile_spam_block_desc(inputs)
	if (locale === "es") return __es.profile_spam_block_desc(inputs)
	if (locale === "fa") return __fa.profile_spam_block_desc(inputs)
	if (locale === "fr") return __fr.profile_spam_block_desc(inputs)
	if (locale === "gu") return __gu.profile_spam_block_desc(inputs)
	if (locale === "he") return __he.profile_spam_block_desc(inputs)
	if (locale === "hi") return __hi.profile_spam_block_desc(inputs)
	if (locale === "id") return __id.profile_spam_block_desc(inputs)
	if (locale === "ja") return __ja.profile_spam_block_desc(inputs)
	if (locale === "kn") return __kn.profile_spam_block_desc(inputs)
	if (locale === "ko") return __ko.profile_spam_block_desc(inputs)
	if (locale === "ku") return __ku.profile_spam_block_desc(inputs)
	if (locale === "ml") return __ml.profile_spam_block_desc(inputs)
	if (locale === "mr") return __mr.profile_spam_block_desc(inputs)
	if (locale === "ne") return __ne.profile_spam_block_desc(inputs)
	if (locale === "or") return __or.profile_spam_block_desc(inputs)
	if (locale === "pa") return __pa.profile_spam_block_desc(inputs)
	if (locale === "pt") return __pt.profile_spam_block_desc(inputs)
	if (locale === "ru") return __ru.profile_spam_block_desc(inputs)
	if (locale === "si") return __si.profile_spam_block_desc(inputs)
	if (locale === "ta") return __ta.profile_spam_block_desc(inputs)
	if (locale === "te") return __te.profile_spam_block_desc(inputs)
	if (locale === "th") return __th.profile_spam_block_desc(inputs)
	if (locale === "tr") return __tr.profile_spam_block_desc(inputs)
	if (locale === "ur") return __ur.profile_spam_block_desc(inputs)
	if (locale === "vi") return __vi.profile_spam_block_desc(inputs)
	return __zh_hans1.profile_spam_block_desc(inputs)
});
/**
* | output |
* | --- |
* | "Posts" |
*
* @param {Profile_PostsInputs} inputs
* @param {{ locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }} options
* @returns {LocalizedString}
*/
export const profile_posts = /** @type {((inputs?: Profile_PostsInputs, options?: { locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }) => LocalizedString) & import('../runtime.js').MessageMetadata<Profile_PostsInputs, { locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }, {}>} */ ((inputs = {}, options = {}) => {
	const locale = experimentalStaticLocale ?? options.locale ?? getLocale()
	if (locale === "en") return __en.profile_posts(inputs)
	if (locale === "ar") return __ar.profile_posts(inputs)
	if (locale === "as") return __as.profile_posts(inputs)
	if (locale === "bn") return __bn.profile_posts(inputs)
	if (locale === "de") return __de.profile_posts(inputs)
	if (locale === "es") return __es.profile_posts(inputs)
	if (locale === "fa") return __fa.profile_posts(inputs)
	if (locale === "fr") return __fr.profile_posts(inputs)
	if (locale === "gu") return __gu.profile_posts(inputs)
	if (locale === "he") return __he.profile_posts(inputs)
	if (locale === "hi") return __hi.profile_posts(inputs)
	if (locale === "id") return __id.profile_posts(inputs)
	if (locale === "ja") return __ja.profile_posts(inputs)
	if (locale === "kn") return __kn.profile_posts(inputs)
	if (locale === "ko") return __ko.profile_posts(inputs)
	if (locale === "ku") return __ku.profile_posts(inputs)
	if (locale === "ml") return __ml.profile_posts(inputs)
	if (locale === "mr") return __mr.profile_posts(inputs)
	if (locale === "ne") return __ne.profile_posts(inputs)
	if (locale === "or") return __or.profile_posts(inputs)
	if (locale === "pa") return __pa.profile_posts(inputs)
	if (locale === "pt") return __pt.profile_posts(inputs)
	if (locale === "ru") return __ru.profile_posts(inputs)
	if (locale === "si") return __si.profile_posts(inputs)
	if (locale === "ta") return __ta.profile_posts(inputs)
	if (locale === "te") return __te.profile_posts(inputs)
	if (locale === "th") return __th.profile_posts(inputs)
	if (locale === "tr") return __tr.profile_posts(inputs)
	if (locale === "ur") return __ur.profile_posts(inputs)
	if (locale === "vi") return __vi.profile_posts(inputs)
	return __zh_hans1.profile_posts(inputs)
});
/**
* | output |
* | --- |
* | "Followers" |
*
* @param {Profile_FollowersInputs} inputs
* @param {{ locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }} options
* @returns {LocalizedString}
*/
export const profile_followers = /** @type {((inputs?: Profile_FollowersInputs, options?: { locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }) => LocalizedString) & import('../runtime.js').MessageMetadata<Profile_FollowersInputs, { locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }, {}>} */ ((inputs = {}, options = {}) => {
	const locale = experimentalStaticLocale ?? options.locale ?? getLocale()
	if (locale === "en") return __en.profile_followers(inputs)
	if (locale === "ar") return __ar.profile_followers(inputs)
	if (locale === "as") return __as.profile_followers(inputs)
	if (locale === "bn") return __bn.profile_followers(inputs)
	if (locale === "de") return __de.profile_followers(inputs)
	if (locale === "es") return __es.profile_followers(inputs)
	if (locale === "fa") return __fa.profile_followers(inputs)
	if (locale === "fr") return __fr.profile_followers(inputs)
	if (locale === "gu") return __gu.profile_followers(inputs)
	if (locale === "he") return __he.profile_followers(inputs)
	if (locale === "hi") return __hi.profile_followers(inputs)
	if (locale === "id") return __id.profile_followers(inputs)
	if (locale === "ja") return __ja.profile_followers(inputs)
	if (locale === "kn") return __kn.profile_followers(inputs)
	if (locale === "ko") return __ko.profile_followers(inputs)
	if (locale === "ku") return __ku.profile_followers(inputs)
	if (locale === "ml") return __ml.profile_followers(inputs)
	if (locale === "mr") return __mr.profile_followers(inputs)
	if (locale === "ne") return __ne.profile_followers(inputs)
	if (locale === "or") return __or.profile_followers(inputs)
	if (locale === "pa") return __pa.profile_followers(inputs)
	if (locale === "pt") return __pt.profile_followers(inputs)
	if (locale === "ru") return __ru.profile_followers(inputs)
	if (locale === "si") return __si.profile_followers(inputs)
	if (locale === "ta") return __ta.profile_followers(inputs)
	if (locale === "te") return __te.profile_followers(inputs)
	if (locale === "th") return __th.profile_followers(inputs)
	if (locale === "tr") return __tr.profile_followers(inputs)
	if (locale === "ur") return __ur.profile_followers(inputs)
	if (locale === "vi") return __vi.profile_followers(inputs)
	return __zh_hans1.profile_followers(inputs)
});
/**
* | output |
* | --- |
* | "Following" |
*
* @param {Profile_FollowingInputs} inputs
* @param {{ locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }} options
* @returns {LocalizedString}
*/
export const profile_following = /** @type {((inputs?: Profile_FollowingInputs, options?: { locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }) => LocalizedString) & import('../runtime.js').MessageMetadata<Profile_FollowingInputs, { locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }, {}>} */ ((inputs = {}, options = {}) => {
	const locale = experimentalStaticLocale ?? options.locale ?? getLocale()
	if (locale === "en") return __en.profile_following(inputs)
	if (locale === "ar") return __ar.profile_following(inputs)
	if (locale === "as") return __as.profile_following(inputs)
	if (locale === "bn") return __bn.profile_following(inputs)
	if (locale === "de") return __de.profile_following(inputs)
	if (locale === "es") return __es.profile_following(inputs)
	if (locale === "fa") return __fa.profile_following(inputs)
	if (locale === "fr") return __fr.profile_following(inputs)
	if (locale === "gu") return __gu.profile_following(inputs)
	if (locale === "he") return __he.profile_following(inputs)
	if (locale === "hi") return __hi.profile_following(inputs)
	if (locale === "id") return __id.profile_following(inputs)
	if (locale === "ja") return __ja.profile_following(inputs)
	if (locale === "kn") return __kn.profile_following(inputs)
	if (locale === "ko") return __ko.profile_following(inputs)
	if (locale === "ku") return __ku.profile_following(inputs)
	if (locale === "ml") return __ml.profile_following(inputs)
	if (locale === "mr") return __mr.profile_following(inputs)
	if (locale === "ne") return __ne.profile_following(inputs)
	if (locale === "or") return __or.profile_following(inputs)
	if (locale === "pa") return __pa.profile_following(inputs)
	if (locale === "pt") return __pt.profile_following(inputs)
	if (locale === "ru") return __ru.profile_following(inputs)
	if (locale === "si") return __si.profile_following(inputs)
	if (locale === "ta") return __ta.profile_following(inputs)
	if (locale === "te") return __te.profile_following(inputs)
	if (locale === "th") return __th.profile_following(inputs)
	if (locale === "tr") return __tr.profile_following(inputs)
	if (locale === "ur") return __ur.profile_following(inputs)
	if (locale === "vi") return __vi.profile_following(inputs)
	return __zh_hans1.profile_following(inputs)
});
/**
* | output |
* | --- |
* | "Follow" |
*
* @param {Profile_FollowInputs} inputs
* @param {{ locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }} options
* @returns {LocalizedString}
*/
export const profile_follow = /** @type {((inputs?: Profile_FollowInputs, options?: { locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }) => LocalizedString) & import('../runtime.js').MessageMetadata<Profile_FollowInputs, { locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }, {}>} */ ((inputs = {}, options = {}) => {
	const locale = experimentalStaticLocale ?? options.locale ?? getLocale()
	if (locale === "en") return __en.profile_follow(inputs)
	if (locale === "ar") return __ar.profile_follow(inputs)
	if (locale === "as") return __as.profile_follow(inputs)
	if (locale === "bn") return __bn.profile_follow(inputs)
	if (locale === "de") return __de.profile_follow(inputs)
	if (locale === "es") return __es.profile_follow(inputs)
	if (locale === "fa") return __fa.profile_follow(inputs)
	if (locale === "fr") return __fr.profile_follow(inputs)
	if (locale === "gu") return __gu.profile_follow(inputs)
	if (locale === "he") return __he.profile_follow(inputs)
	if (locale === "hi") return __hi.profile_follow(inputs)
	if (locale === "id") return __id.profile_follow(inputs)
	if (locale === "ja") return __ja.profile_follow(inputs)
	if (locale === "kn") return __kn.profile_follow(inputs)
	if (locale === "ko") return __ko.profile_follow(inputs)
	if (locale === "ku") return __ku.profile_follow(inputs)
	if (locale === "ml") return __ml.profile_follow(inputs)
	if (locale === "mr") return __mr.profile_follow(inputs)
	if (locale === "ne") return __ne.profile_follow(inputs)
	if (locale === "or") return __or.profile_follow(inputs)
	if (locale === "pa") return __pa.profile_follow(inputs)
	if (locale === "pt") return __pt.profile_follow(inputs)
	if (locale === "ru") return __ru.profile_follow(inputs)
	if (locale === "si") return __si.profile_follow(inputs)
	if (locale === "ta") return __ta.profile_follow(inputs)
	if (locale === "te") return __te.profile_follow(inputs)
	if (locale === "th") return __th.profile_follow(inputs)
	if (locale === "tr") return __tr.profile_follow(inputs)
	if (locale === "ur") return __ur.profile_follow(inputs)
	if (locale === "vi") return __vi.profile_follow(inputs)
	return __zh_hans1.profile_follow(inputs)
});
/**
* | output |
* | --- |
* | "Unfollow" |
*
* @param {Profile_UnfollowInputs} inputs
* @param {{ locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }} options
* @returns {LocalizedString}
*/
export const profile_unfollow = /** @type {((inputs?: Profile_UnfollowInputs, options?: { locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }) => LocalizedString) & import('../runtime.js').MessageMetadata<Profile_UnfollowInputs, { locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }, {}>} */ ((inputs = {}, options = {}) => {
	const locale = experimentalStaticLocale ?? options.locale ?? getLocale()
	if (locale === "en") return __en.profile_unfollow(inputs)
	if (locale === "ar") return __ar.profile_unfollow(inputs)
	if (locale === "as") return __as.profile_unfollow(inputs)
	if (locale === "bn") return __bn.profile_unfollow(inputs)
	if (locale === "de") return __de.profile_unfollow(inputs)
	if (locale === "es") return __es.profile_unfollow(inputs)
	if (locale === "fa") return __fa.profile_unfollow(inputs)
	if (locale === "fr") return __fr.profile_unfollow(inputs)
	if (locale === "gu") return __gu.profile_unfollow(inputs)
	if (locale === "he") return __he.profile_unfollow(inputs)
	if (locale === "hi") return __hi.profile_unfollow(inputs)
	if (locale === "id") return __id.profile_unfollow(inputs)
	if (locale === "ja") return __ja.profile_unfollow(inputs)
	if (locale === "kn") return __kn.profile_unfollow(inputs)
	if (locale === "ko") return __ko.profile_unfollow(inputs)
	if (locale === "ku") return __ku.profile_unfollow(inputs)
	if (locale === "ml") return __ml.profile_unfollow(inputs)
	if (locale === "mr") return __mr.profile_unfollow(inputs)
	if (locale === "ne") return __ne.profile_unfollow(inputs)
	if (locale === "or") return __or.profile_unfollow(inputs)
	if (locale === "pa") return __pa.profile_unfollow(inputs)
	if (locale === "pt") return __pt.profile_unfollow(inputs)
	if (locale === "ru") return __ru.profile_unfollow(inputs)
	if (locale === "si") return __si.profile_unfollow(inputs)
	if (locale === "ta") return __ta.profile_unfollow(inputs)
	if (locale === "te") return __te.profile_unfollow(inputs)
	if (locale === "th") return __th.profile_unfollow(inputs)
	if (locale === "tr") return __tr.profile_unfollow(inputs)
	if (locale === "ur") return __ur.profile_unfollow(inputs)
	if (locale === "vi") return __vi.profile_unfollow(inputs)
	return __zh_hans1.profile_unfollow(inputs)
});
/**
* | output |
* | --- |
* | "Message" |
*
* @param {Profile_MessageInputs} inputs
* @param {{ locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }} options
* @returns {LocalizedString}
*/
export const profile_message = /** @type {((inputs?: Profile_MessageInputs, options?: { locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }) => LocalizedString) & import('../runtime.js').MessageMetadata<Profile_MessageInputs, { locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }, {}>} */ ((inputs = {}, options = {}) => {
	const locale = experimentalStaticLocale ?? options.locale ?? getLocale()
	if (locale === "en") return __en.profile_message(inputs)
	if (locale === "ar") return __ar.profile_message(inputs)
	if (locale === "as") return __as.profile_message(inputs)
	if (locale === "bn") return __bn.profile_message(inputs)
	if (locale === "de") return __de.profile_message(inputs)
	if (locale === "es") return __es.profile_message(inputs)
	if (locale === "fa") return __fa.profile_message(inputs)
	if (locale === "fr") return __fr.profile_message(inputs)
	if (locale === "gu") return __gu.profile_message(inputs)
	if (locale === "he") return __he.profile_message(inputs)
	if (locale === "hi") return __hi.profile_message(inputs)
	if (locale === "id") return __id.profile_message(inputs)
	if (locale === "ja") return __ja.profile_message(inputs)
	if (locale === "kn") return __kn.profile_message(inputs)
	if (locale === "ko") return __ko.profile_message(inputs)
	if (locale === "ku") return __ku.profile_message(inputs)
	if (locale === "ml") return __ml.profile_message(inputs)
	if (locale === "mr") return __mr.profile_message(inputs)
	if (locale === "ne") return __ne.profile_message(inputs)
	if (locale === "or") return __or.profile_message(inputs)
	if (locale === "pa") return __pa.profile_message(inputs)
	if (locale === "pt") return __pt.profile_message(inputs)
	if (locale === "ru") return __ru.profile_message(inputs)
	if (locale === "si") return __si.profile_message(inputs)
	if (locale === "ta") return __ta.profile_message(inputs)
	if (locale === "te") return __te.profile_message(inputs)
	if (locale === "th") return __th.profile_message(inputs)
	if (locale === "tr") return __tr.profile_message(inputs)
	if (locale === "ur") return __ur.profile_message(inputs)
	if (locale === "vi") return __vi.profile_message(inputs)
	return __zh_hans1.profile_message(inputs)
});
/**
* | output |
* | --- |
* | "Edit Profile" |
*
* @param {Profile_EditInputs} inputs
* @param {{ locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }} options
* @returns {LocalizedString}
*/
export const profile_edit = /** @type {((inputs?: Profile_EditInputs, options?: { locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }) => LocalizedString) & import('../runtime.js').MessageMetadata<Profile_EditInputs, { locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }, {}>} */ ((inputs = {}, options = {}) => {
	const locale = experimentalStaticLocale ?? options.locale ?? getLocale()
	if (locale === "en") return __en.profile_edit(inputs)
	if (locale === "ar") return __ar.profile_edit(inputs)
	if (locale === "as") return __as.profile_edit(inputs)
	if (locale === "bn") return __bn.profile_edit(inputs)
	if (locale === "de") return __de.profile_edit(inputs)
	if (locale === "es") return __es.profile_edit(inputs)
	if (locale === "fa") return __fa.profile_edit(inputs)
	if (locale === "fr") return __fr.profile_edit(inputs)
	if (locale === "gu") return __gu.profile_edit(inputs)
	if (locale === "he") return __he.profile_edit(inputs)
	if (locale === "hi") return __hi.profile_edit(inputs)
	if (locale === "id") return __id.profile_edit(inputs)
	if (locale === "ja") return __ja.profile_edit(inputs)
	if (locale === "kn") return __kn.profile_edit(inputs)
	if (locale === "ko") return __ko.profile_edit(inputs)
	if (locale === "ku") return __ku.profile_edit(inputs)
	if (locale === "ml") return __ml.profile_edit(inputs)
	if (locale === "mr") return __mr.profile_edit(inputs)
	if (locale === "ne") return __ne.profile_edit(inputs)
	if (locale === "or") return __or.profile_edit(inputs)
	if (locale === "pa") return __pa.profile_edit(inputs)
	if (locale === "pt") return __pt.profile_edit(inputs)
	if (locale === "ru") return __ru.profile_edit(inputs)
	if (locale === "si") return __si.profile_edit(inputs)
	if (locale === "ta") return __ta.profile_edit(inputs)
	if (locale === "te") return __te.profile_edit(inputs)
	if (locale === "th") return __th.profile_edit(inputs)
	if (locale === "tr") return __tr.profile_edit(inputs)
	if (locale === "ur") return __ur.profile_edit(inputs)
	if (locale === "vi") return __vi.profile_edit(inputs)
	return __zh_hans1.profile_edit(inputs)
});
/**
* | output |
* | --- |
* | "Actors" |
*
* @param {Search_ActorsInputs} inputs
* @param {{ locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }} options
* @returns {LocalizedString}
*/
export const search_actors = /** @type {((inputs?: Search_ActorsInputs, options?: { locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }) => LocalizedString) & import('../runtime.js').MessageMetadata<Search_ActorsInputs, { locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }, {}>} */ ((inputs = {}, options = {}) => {
	const locale = experimentalStaticLocale ?? options.locale ?? getLocale()
	if (locale === "en") return __en.search_actors(inputs)
	if (locale === "ar") return __ar.search_actors(inputs)
	if (locale === "as") return __as.search_actors(inputs)
	if (locale === "bn") return __bn.search_actors(inputs)
	if (locale === "de") return __de.search_actors(inputs)
	if (locale === "es") return __es.search_actors(inputs)
	if (locale === "fa") return __fa.search_actors(inputs)
	if (locale === "fr") return __fr.search_actors(inputs)
	if (locale === "gu") return __gu.search_actors(inputs)
	if (locale === "he") return __he.search_actors(inputs)
	if (locale === "hi") return __hi.search_actors(inputs)
	if (locale === "id") return __id.search_actors(inputs)
	if (locale === "ja") return __ja.search_actors(inputs)
	if (locale === "kn") return __kn.search_actors(inputs)
	if (locale === "ko") return __ko.search_actors(inputs)
	if (locale === "ku") return __ku.search_actors(inputs)
	if (locale === "ml") return __ml.search_actors(inputs)
	if (locale === "mr") return __mr.search_actors(inputs)
	if (locale === "ne") return __ne.search_actors(inputs)
	if (locale === "or") return __or.search_actors(inputs)
	if (locale === "pa") return __pa.search_actors(inputs)
	if (locale === "pt") return __pt.search_actors(inputs)
	if (locale === "ru") return __ru.search_actors(inputs)
	if (locale === "si") return __si.search_actors(inputs)
	if (locale === "ta") return __ta.search_actors(inputs)
	if (locale === "te") return __te.search_actors(inputs)
	if (locale === "th") return __th.search_actors(inputs)
	if (locale === "tr") return __tr.search_actors(inputs)
	if (locale === "ur") return __ur.search_actors(inputs)
	if (locale === "vi") return __vi.search_actors(inputs)
	return __zh_hans1.search_actors(inputs)
});
/**
* | output |
* | --- |
* | "Posts" |
*
* @param {Search_PostsInputs} inputs
* @param {{ locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }} options
* @returns {LocalizedString}
*/
export const search_posts = /** @type {((inputs?: Search_PostsInputs, options?: { locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }) => LocalizedString) & import('../runtime.js').MessageMetadata<Search_PostsInputs, { locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }, {}>} */ ((inputs = {}, options = {}) => {
	const locale = experimentalStaticLocale ?? options.locale ?? getLocale()
	if (locale === "en") return __en.search_posts(inputs)
	if (locale === "ar") return __ar.search_posts(inputs)
	if (locale === "as") return __as.search_posts(inputs)
	if (locale === "bn") return __bn.search_posts(inputs)
	if (locale === "de") return __de.search_posts(inputs)
	if (locale === "es") return __es.search_posts(inputs)
	if (locale === "fa") return __fa.search_posts(inputs)
	if (locale === "fr") return __fr.search_posts(inputs)
	if (locale === "gu") return __gu.search_posts(inputs)
	if (locale === "he") return __he.search_posts(inputs)
	if (locale === "hi") return __hi.search_posts(inputs)
	if (locale === "id") return __id.search_posts(inputs)
	if (locale === "ja") return __ja.search_posts(inputs)
	if (locale === "kn") return __kn.search_posts(inputs)
	if (locale === "ko") return __ko.search_posts(inputs)
	if (locale === "ku") return __ku.search_posts(inputs)
	if (locale === "ml") return __ml.search_posts(inputs)
	if (locale === "mr") return __mr.search_posts(inputs)
	if (locale === "ne") return __ne.search_posts(inputs)
	if (locale === "or") return __or.search_posts(inputs)
	if (locale === "pa") return __pa.search_posts(inputs)
	if (locale === "pt") return __pt.search_posts(inputs)
	if (locale === "ru") return __ru.search_posts(inputs)
	if (locale === "si") return __si.search_posts(inputs)
	if (locale === "ta") return __ta.search_posts(inputs)
	if (locale === "te") return __te.search_posts(inputs)
	if (locale === "th") return __th.search_posts(inputs)
	if (locale === "tr") return __tr.search_posts(inputs)
	if (locale === "ur") return __ur.search_posts(inputs)
	if (locale === "vi") return __vi.search_posts(inputs)
	return __zh_hans1.search_posts(inputs)
});
/**
* | output |
* | --- |
* | "People" |
*
* @param {Search_PeopleInputs} inputs
* @param {{ locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }} options
* @returns {LocalizedString}
*/
export const search_people = /** @type {((inputs?: Search_PeopleInputs, options?: { locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }) => LocalizedString) & import('../runtime.js').MessageMetadata<Search_PeopleInputs, { locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }, {}>} */ ((inputs = {}, options = {}) => {
	const locale = experimentalStaticLocale ?? options.locale ?? getLocale()
	if (locale === "en") return __en.search_people(inputs)
	if (locale === "ar") return __ar.search_people(inputs)
	if (locale === "as") return __as.search_people(inputs)
	if (locale === "bn") return __bn.search_people(inputs)
	if (locale === "de") return __de.search_people(inputs)
	if (locale === "es") return __es.search_people(inputs)
	if (locale === "fa") return __fa.search_people(inputs)
	if (locale === "fr") return __fr.search_people(inputs)
	if (locale === "gu") return __gu.search_people(inputs)
	if (locale === "he") return __he.search_people(inputs)
	if (locale === "hi") return __hi.search_people(inputs)
	if (locale === "id") return __id.search_people(inputs)
	if (locale === "ja") return __ja.search_people(inputs)
	if (locale === "kn") return __kn.search_people(inputs)
	if (locale === "ko") return __ko.search_people(inputs)
	if (locale === "ku") return __ku.search_people(inputs)
	if (locale === "ml") return __ml.search_people(inputs)
	if (locale === "mr") return __mr.search_people(inputs)
	if (locale === "ne") return __ne.search_people(inputs)
	if (locale === "or") return __or.search_people(inputs)
	if (locale === "pa") return __pa.search_people(inputs)
	if (locale === "pt") return __pt.search_people(inputs)
	if (locale === "ru") return __ru.search_people(inputs)
	if (locale === "si") return __si.search_people(inputs)
	if (locale === "ta") return __ta.search_people(inputs)
	if (locale === "te") return __te.search_people(inputs)
	if (locale === "th") return __th.search_people(inputs)
	if (locale === "tr") return __tr.search_people(inputs)
	if (locale === "ur") return __ur.search_people(inputs)
	if (locale === "vi") return __vi.search_people(inputs)
	return __zh_hans1.search_people(inputs)
});
/**
* | output |
* | --- |
* | "Search YORO" |
*
* @param {Search_PlaceholderInputs} inputs
* @param {{ locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }} options
* @returns {LocalizedString}
*/
export const search_placeholder = /** @type {((inputs?: Search_PlaceholderInputs, options?: { locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }) => LocalizedString) & import('../runtime.js').MessageMetadata<Search_PlaceholderInputs, { locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }, {}>} */ ((inputs = {}, options = {}) => {
	const locale = experimentalStaticLocale ?? options.locale ?? getLocale()
	if (locale === "en") return __en.search_placeholder(inputs)
	if (locale === "ar") return __ar.search_placeholder(inputs)
	if (locale === "as") return __as.search_placeholder(inputs)
	if (locale === "bn") return __bn.search_placeholder(inputs)
	if (locale === "de") return __de.search_placeholder(inputs)
	if (locale === "es") return __es.search_placeholder(inputs)
	if (locale === "fa") return __fa.search_placeholder(inputs)
	if (locale === "fr") return __fr.search_placeholder(inputs)
	if (locale === "gu") return __gu.search_placeholder(inputs)
	if (locale === "he") return __he.search_placeholder(inputs)
	if (locale === "hi") return __hi.search_placeholder(inputs)
	if (locale === "id") return __id.search_placeholder(inputs)
	if (locale === "ja") return __ja.search_placeholder(inputs)
	if (locale === "kn") return __kn.search_placeholder(inputs)
	if (locale === "ko") return __ko.search_placeholder(inputs)
	if (locale === "ku") return __ku.search_placeholder(inputs)
	if (locale === "ml") return __ml.search_placeholder(inputs)
	if (locale === "mr") return __mr.search_placeholder(inputs)
	if (locale === "ne") return __ne.search_placeholder(inputs)
	if (locale === "or") return __or.search_placeholder(inputs)
	if (locale === "pa") return __pa.search_placeholder(inputs)
	if (locale === "pt") return __pt.search_placeholder(inputs)
	if (locale === "ru") return __ru.search_placeholder(inputs)
	if (locale === "si") return __si.search_placeholder(inputs)
	if (locale === "ta") return __ta.search_placeholder(inputs)
	if (locale === "te") return __te.search_placeholder(inputs)
	if (locale === "th") return __th.search_placeholder(inputs)
	if (locale === "tr") return __tr.search_placeholder(inputs)
	if (locale === "ur") return __ur.search_placeholder(inputs)
	if (locale === "vi") return __vi.search_placeholder(inputs)
	return __zh_hans1.search_placeholder(inputs)
});
/**
* | output |
* | --- |
* | "Discover" |
*
* @param {Feed_DiscoverInputs} inputs
* @param {{ locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }} options
* @returns {LocalizedString}
*/
export const feed_discover = /** @type {((inputs?: Feed_DiscoverInputs, options?: { locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }) => LocalizedString) & import('../runtime.js').MessageMetadata<Feed_DiscoverInputs, { locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }, {}>} */ ((inputs = {}, options = {}) => {
	const locale = experimentalStaticLocale ?? options.locale ?? getLocale()
	if (locale === "en") return __en.feed_discover(inputs)
	if (locale === "ar") return __ar.feed_discover(inputs)
	if (locale === "as") return __as.feed_discover(inputs)
	if (locale === "bn") return __bn.feed_discover(inputs)
	if (locale === "de") return __de.feed_discover(inputs)
	if (locale === "es") return __es.feed_discover(inputs)
	if (locale === "fa") return __fa.feed_discover(inputs)
	if (locale === "fr") return __fr.feed_discover(inputs)
	if (locale === "gu") return __gu.feed_discover(inputs)
	if (locale === "he") return __he.feed_discover(inputs)
	if (locale === "hi") return __hi.feed_discover(inputs)
	if (locale === "id") return __id.feed_discover(inputs)
	if (locale === "ja") return __ja.feed_discover(inputs)
	if (locale === "kn") return __kn.feed_discover(inputs)
	if (locale === "ko") return __ko.feed_discover(inputs)
	if (locale === "ku") return __ku.feed_discover(inputs)
	if (locale === "ml") return __ml.feed_discover(inputs)
	if (locale === "mr") return __mr.feed_discover(inputs)
	if (locale === "ne") return __ne.feed_discover(inputs)
	if (locale === "or") return __or.feed_discover(inputs)
	if (locale === "pa") return __pa.feed_discover(inputs)
	if (locale === "pt") return __pt.feed_discover(inputs)
	if (locale === "ru") return __ru.feed_discover(inputs)
	if (locale === "si") return __si.feed_discover(inputs)
	if (locale === "ta") return __ta.feed_discover(inputs)
	if (locale === "te") return __te.feed_discover(inputs)
	if (locale === "th") return __th.feed_discover(inputs)
	if (locale === "tr") return __tr.feed_discover(inputs)
	if (locale === "ur") return __ur.feed_discover(inputs)
	if (locale === "vi") return __vi.feed_discover(inputs)
	return __zh_hans1.feed_discover(inputs)
});
/**
* | output |
* | --- |
* | "Following" |
*
* @param {Feed_FollowingInputs} inputs
* @param {{ locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }} options
* @returns {LocalizedString}
*/
export const feed_following = /** @type {((inputs?: Feed_FollowingInputs, options?: { locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }) => LocalizedString) & import('../runtime.js').MessageMetadata<Feed_FollowingInputs, { locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }, {}>} */ ((inputs = {}, options = {}) => {
	const locale = experimentalStaticLocale ?? options.locale ?? getLocale()
	if (locale === "en") return __en.feed_following(inputs)
	if (locale === "ar") return __ar.feed_following(inputs)
	if (locale === "as") return __as.feed_following(inputs)
	if (locale === "bn") return __bn.feed_following(inputs)
	if (locale === "de") return __de.feed_following(inputs)
	if (locale === "es") return __es.feed_following(inputs)
	if (locale === "fa") return __fa.feed_following(inputs)
	if (locale === "fr") return __fr.feed_following(inputs)
	if (locale === "gu") return __gu.feed_following(inputs)
	if (locale === "he") return __he.feed_following(inputs)
	if (locale === "hi") return __hi.feed_following(inputs)
	if (locale === "id") return __id.feed_following(inputs)
	if (locale === "ja") return __ja.feed_following(inputs)
	if (locale === "kn") return __kn.feed_following(inputs)
	if (locale === "ko") return __ko.feed_following(inputs)
	if (locale === "ku") return __ku.feed_following(inputs)
	if (locale === "ml") return __ml.feed_following(inputs)
	if (locale === "mr") return __mr.feed_following(inputs)
	if (locale === "ne") return __ne.feed_following(inputs)
	if (locale === "or") return __or.feed_following(inputs)
	if (locale === "pa") return __pa.feed_following(inputs)
	if (locale === "pt") return __pt.feed_following(inputs)
	if (locale === "ru") return __ru.feed_following(inputs)
	if (locale === "si") return __si.feed_following(inputs)
	if (locale === "ta") return __ta.feed_following(inputs)
	if (locale === "te") return __te.feed_following(inputs)
	if (locale === "th") return __th.feed_following(inputs)
	if (locale === "tr") return __tr.feed_following(inputs)
	if (locale === "ur") return __ur.feed_following(inputs)
	if (locale === "vi") return __vi.feed_following(inputs)
	return __zh_hans1.feed_following(inputs)
});
/**
* | output |
* | --- |
* | "No posts yet" |
*
* @param {Feed_EmptyInputs} inputs
* @param {{ locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }} options
* @returns {LocalizedString}
*/
export const feed_empty = /** @type {((inputs?: Feed_EmptyInputs, options?: { locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }) => LocalizedString) & import('../runtime.js').MessageMetadata<Feed_EmptyInputs, { locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }, {}>} */ ((inputs = {}, options = {}) => {
	const locale = experimentalStaticLocale ?? options.locale ?? getLocale()
	if (locale === "en") return __en.feed_empty(inputs)
	if (locale === "ar") return __ar.feed_empty(inputs)
	if (locale === "as") return __as.feed_empty(inputs)
	if (locale === "bn") return __bn.feed_empty(inputs)
	if (locale === "de") return __de.feed_empty(inputs)
	if (locale === "es") return __es.feed_empty(inputs)
	if (locale === "fa") return __fa.feed_empty(inputs)
	if (locale === "fr") return __fr.feed_empty(inputs)
	if (locale === "gu") return __gu.feed_empty(inputs)
	if (locale === "he") return __he.feed_empty(inputs)
	if (locale === "hi") return __hi.feed_empty(inputs)
	if (locale === "id") return __id.feed_empty(inputs)
	if (locale === "ja") return __ja.feed_empty(inputs)
	if (locale === "kn") return __kn.feed_empty(inputs)
	if (locale === "ko") return __ko.feed_empty(inputs)
	if (locale === "ku") return __ku.feed_empty(inputs)
	if (locale === "ml") return __ml.feed_empty(inputs)
	if (locale === "mr") return __mr.feed_empty(inputs)
	if (locale === "ne") return __ne.feed_empty(inputs)
	if (locale === "or") return __or.feed_empty(inputs)
	if (locale === "pa") return __pa.feed_empty(inputs)
	if (locale === "pt") return __pt.feed_empty(inputs)
	if (locale === "ru") return __ru.feed_empty(inputs)
	if (locale === "si") return __si.feed_empty(inputs)
	if (locale === "ta") return __ta.feed_empty(inputs)
	if (locale === "te") return __te.feed_empty(inputs)
	if (locale === "th") return __th.feed_empty(inputs)
	if (locale === "tr") return __tr.feed_empty(inputs)
	if (locale === "ur") return __ur.feed_empty(inputs)
	if (locale === "vi") return __vi.feed_empty(inputs)
	return __zh_hans1.feed_empty(inputs)
});
/**
* | output |
* | --- |
* | "Loading..." |
*
* @param {Feed_LoadingInputs} inputs
* @param {{ locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }} options
* @returns {LocalizedString}
*/
export const feed_loading = /** @type {((inputs?: Feed_LoadingInputs, options?: { locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }) => LocalizedString) & import('../runtime.js').MessageMetadata<Feed_LoadingInputs, { locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }, {}>} */ ((inputs = {}, options = {}) => {
	const locale = experimentalStaticLocale ?? options.locale ?? getLocale()
	if (locale === "en") return __en.feed_loading(inputs)
	if (locale === "ar") return __ar.feed_loading(inputs)
	if (locale === "as") return __as.feed_loading(inputs)
	if (locale === "bn") return __bn.feed_loading(inputs)
	if (locale === "de") return __de.feed_loading(inputs)
	if (locale === "es") return __es.feed_loading(inputs)
	if (locale === "fa") return __fa.feed_loading(inputs)
	if (locale === "fr") return __fr.feed_loading(inputs)
	if (locale === "gu") return __gu.feed_loading(inputs)
	if (locale === "he") return __he.feed_loading(inputs)
	if (locale === "hi") return __hi.feed_loading(inputs)
	if (locale === "id") return __id.feed_loading(inputs)
	if (locale === "ja") return __ja.feed_loading(inputs)
	if (locale === "kn") return __kn.feed_loading(inputs)
	if (locale === "ko") return __ko.feed_loading(inputs)
	if (locale === "ku") return __ku.feed_loading(inputs)
	if (locale === "ml") return __ml.feed_loading(inputs)
	if (locale === "mr") return __mr.feed_loading(inputs)
	if (locale === "ne") return __ne.feed_loading(inputs)
	if (locale === "or") return __or.feed_loading(inputs)
	if (locale === "pa") return __pa.feed_loading(inputs)
	if (locale === "pt") return __pt.feed_loading(inputs)
	if (locale === "ru") return __ru.feed_loading(inputs)
	if (locale === "si") return __si.feed_loading(inputs)
	if (locale === "ta") return __ta.feed_loading(inputs)
	if (locale === "te") return __te.feed_loading(inputs)
	if (locale === "th") return __th.feed_loading(inputs)
	if (locale === "tr") return __tr.feed_loading(inputs)
	if (locale === "ur") return __ur.feed_loading(inputs)
	if (locale === "vi") return __vi.feed_loading(inputs)
	return __zh_hans1.feed_loading(inputs)
});
/**
* | output |
* | --- |
* | "Retry" |
*
* @param {Feed_Error_RetryInputs} inputs
* @param {{ locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }} options
* @returns {LocalizedString}
*/
export const feed_error_retry = /** @type {((inputs?: Feed_Error_RetryInputs, options?: { locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }) => LocalizedString) & import('../runtime.js').MessageMetadata<Feed_Error_RetryInputs, { locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }, {}>} */ ((inputs = {}, options = {}) => {
	const locale = experimentalStaticLocale ?? options.locale ?? getLocale()
	if (locale === "en") return __en.feed_error_retry(inputs)
	if (locale === "ar") return __ar.feed_error_retry(inputs)
	if (locale === "as") return __as.feed_error_retry(inputs)
	if (locale === "bn") return __bn.feed_error_retry(inputs)
	if (locale === "de") return __de.feed_error_retry(inputs)
	if (locale === "es") return __es.feed_error_retry(inputs)
	if (locale === "fa") return __fa.feed_error_retry(inputs)
	if (locale === "fr") return __fr.feed_error_retry(inputs)
	if (locale === "gu") return __gu.feed_error_retry(inputs)
	if (locale === "he") return __he.feed_error_retry(inputs)
	if (locale === "hi") return __hi.feed_error_retry(inputs)
	if (locale === "id") return __id.feed_error_retry(inputs)
	if (locale === "ja") return __ja.feed_error_retry(inputs)
	if (locale === "kn") return __kn.feed_error_retry(inputs)
	if (locale === "ko") return __ko.feed_error_retry(inputs)
	if (locale === "ku") return __ku.feed_error_retry(inputs)
	if (locale === "ml") return __ml.feed_error_retry(inputs)
	if (locale === "mr") return __mr.feed_error_retry(inputs)
	if (locale === "ne") return __ne.feed_error_retry(inputs)
	if (locale === "or") return __or.feed_error_retry(inputs)
	if (locale === "pa") return __pa.feed_error_retry(inputs)
	if (locale === "pt") return __pt.feed_error_retry(inputs)
	if (locale === "ru") return __ru.feed_error_retry(inputs)
	if (locale === "si") return __si.feed_error_retry(inputs)
	if (locale === "ta") return __ta.feed_error_retry(inputs)
	if (locale === "te") return __te.feed_error_retry(inputs)
	if (locale === "th") return __th.feed_error_retry(inputs)
	if (locale === "tr") return __tr.feed_error_retry(inputs)
	if (locale === "ur") return __ur.feed_error_retry(inputs)
	if (locale === "vi") return __vi.feed_error_retry(inputs)
	return __zh_hans1.feed_error_retry(inputs)
});
/**
* | output |
* | --- |
* | "What's happening?" |
*
* @param {Compose_PlaceholderInputs} inputs
* @param {{ locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }} options
* @returns {LocalizedString}
*/
export const compose_placeholder = /** @type {((inputs?: Compose_PlaceholderInputs, options?: { locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }) => LocalizedString) & import('../runtime.js').MessageMetadata<Compose_PlaceholderInputs, { locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }, {}>} */ ((inputs = {}, options = {}) => {
	const locale = experimentalStaticLocale ?? options.locale ?? getLocale()
	if (locale === "en") return __en.compose_placeholder(inputs)
	if (locale === "ar") return __ar.compose_placeholder(inputs)
	if (locale === "as") return __as.compose_placeholder(inputs)
	if (locale === "bn") return __bn.compose_placeholder(inputs)
	if (locale === "de") return __de.compose_placeholder(inputs)
	if (locale === "es") return __es.compose_placeholder(inputs)
	if (locale === "fa") return __fa.compose_placeholder(inputs)
	if (locale === "fr") return __fr.compose_placeholder(inputs)
	if (locale === "gu") return __gu.compose_placeholder(inputs)
	if (locale === "he") return __he.compose_placeholder(inputs)
	if (locale === "hi") return __hi.compose_placeholder(inputs)
	if (locale === "id") return __id.compose_placeholder(inputs)
	if (locale === "ja") return __ja.compose_placeholder(inputs)
	if (locale === "kn") return __kn.compose_placeholder(inputs)
	if (locale === "ko") return __ko.compose_placeholder(inputs)
	if (locale === "ku") return __ku.compose_placeholder(inputs)
	if (locale === "ml") return __ml.compose_placeholder(inputs)
	if (locale === "mr") return __mr.compose_placeholder(inputs)
	if (locale === "ne") return __ne.compose_placeholder(inputs)
	if (locale === "or") return __or.compose_placeholder(inputs)
	if (locale === "pa") return __pa.compose_placeholder(inputs)
	if (locale === "pt") return __pt.compose_placeholder(inputs)
	if (locale === "ru") return __ru.compose_placeholder(inputs)
	if (locale === "si") return __si.compose_placeholder(inputs)
	if (locale === "ta") return __ta.compose_placeholder(inputs)
	if (locale === "te") return __te.compose_placeholder(inputs)
	if (locale === "th") return __th.compose_placeholder(inputs)
	if (locale === "tr") return __tr.compose_placeholder(inputs)
	if (locale === "ur") return __ur.compose_placeholder(inputs)
	if (locale === "vi") return __vi.compose_placeholder(inputs)
	return __zh_hans1.compose_placeholder(inputs)
});
/**
* | output |
* | --- |
* | "Post" |
*
* @param {Compose_PostInputs} inputs
* @param {{ locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }} options
* @returns {LocalizedString}
*/
export const compose_post = /** @type {((inputs?: Compose_PostInputs, options?: { locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }) => LocalizedString) & import('../runtime.js').MessageMetadata<Compose_PostInputs, { locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }, {}>} */ ((inputs = {}, options = {}) => {
	const locale = experimentalStaticLocale ?? options.locale ?? getLocale()
	if (locale === "en") return __en.compose_post(inputs)
	if (locale === "ar") return __ar.compose_post(inputs)
	if (locale === "as") return __as.compose_post(inputs)
	if (locale === "bn") return __bn.compose_post(inputs)
	if (locale === "de") return __de.compose_post(inputs)
	if (locale === "es") return __es.compose_post(inputs)
	if (locale === "fa") return __fa.compose_post(inputs)
	if (locale === "fr") return __fr.compose_post(inputs)
	if (locale === "gu") return __gu.compose_post(inputs)
	if (locale === "he") return __he.compose_post(inputs)
	if (locale === "hi") return __hi.compose_post(inputs)
	if (locale === "id") return __id.compose_post(inputs)
	if (locale === "ja") return __ja.compose_post(inputs)
	if (locale === "kn") return __kn.compose_post(inputs)
	if (locale === "ko") return __ko.compose_post(inputs)
	if (locale === "ku") return __ku.compose_post(inputs)
	if (locale === "ml") return __ml.compose_post(inputs)
	if (locale === "mr") return __mr.compose_post(inputs)
	if (locale === "ne") return __ne.compose_post(inputs)
	if (locale === "or") return __or.compose_post(inputs)
	if (locale === "pa") return __pa.compose_post(inputs)
	if (locale === "pt") return __pt.compose_post(inputs)
	if (locale === "ru") return __ru.compose_post(inputs)
	if (locale === "si") return __si.compose_post(inputs)
	if (locale === "ta") return __ta.compose_post(inputs)
	if (locale === "te") return __te.compose_post(inputs)
	if (locale === "th") return __th.compose_post(inputs)
	if (locale === "tr") return __tr.compose_post(inputs)
	if (locale === "ur") return __ur.compose_post(inputs)
	if (locale === "vi") return __vi.compose_post(inputs)
	return __zh_hans1.compose_post(inputs)
});
/**
* | output |
* | --- |
* | "Cancel" |
*
* @param {Compose_CancelInputs} inputs
* @param {{ locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }} options
* @returns {LocalizedString}
*/
export const compose_cancel = /** @type {((inputs?: Compose_CancelInputs, options?: { locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }) => LocalizedString) & import('../runtime.js').MessageMetadata<Compose_CancelInputs, { locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }, {}>} */ ((inputs = {}, options = {}) => {
	const locale = experimentalStaticLocale ?? options.locale ?? getLocale()
	if (locale === "en") return __en.compose_cancel(inputs)
	if (locale === "ar") return __ar.compose_cancel(inputs)
	if (locale === "as") return __as.compose_cancel(inputs)
	if (locale === "bn") return __bn.compose_cancel(inputs)
	if (locale === "de") return __de.compose_cancel(inputs)
	if (locale === "es") return __es.compose_cancel(inputs)
	if (locale === "fa") return __fa.compose_cancel(inputs)
	if (locale === "fr") return __fr.compose_cancel(inputs)
	if (locale === "gu") return __gu.compose_cancel(inputs)
	if (locale === "he") return __he.compose_cancel(inputs)
	if (locale === "hi") return __hi.compose_cancel(inputs)
	if (locale === "id") return __id.compose_cancel(inputs)
	if (locale === "ja") return __ja.compose_cancel(inputs)
	if (locale === "kn") return __kn.compose_cancel(inputs)
	if (locale === "ko") return __ko.compose_cancel(inputs)
	if (locale === "ku") return __ku.compose_cancel(inputs)
	if (locale === "ml") return __ml.compose_cancel(inputs)
	if (locale === "mr") return __mr.compose_cancel(inputs)
	if (locale === "ne") return __ne.compose_cancel(inputs)
	if (locale === "or") return __or.compose_cancel(inputs)
	if (locale === "pa") return __pa.compose_cancel(inputs)
	if (locale === "pt") return __pt.compose_cancel(inputs)
	if (locale === "ru") return __ru.compose_cancel(inputs)
	if (locale === "si") return __si.compose_cancel(inputs)
	if (locale === "ta") return __ta.compose_cancel(inputs)
	if (locale === "te") return __te.compose_cancel(inputs)
	if (locale === "th") return __th.compose_cancel(inputs)
	if (locale === "tr") return __tr.compose_cancel(inputs)
	if (locale === "ur") return __ur.compose_cancel(inputs)
	if (locale === "vi") return __vi.compose_cancel(inputs)
	return __zh_hans1.compose_cancel(inputs)
});
/**
* | output |
* | --- |
* | "New Message" |
*
* @param {Convo_New_MessageInputs} inputs
* @param {{ locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }} options
* @returns {LocalizedString}
*/
export const convo_new_message = /** @type {((inputs?: Convo_New_MessageInputs, options?: { locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }) => LocalizedString) & import('../runtime.js').MessageMetadata<Convo_New_MessageInputs, { locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }, {}>} */ ((inputs = {}, options = {}) => {
	const locale = experimentalStaticLocale ?? options.locale ?? getLocale()
	if (locale === "en") return __en.convo_new_message(inputs)
	if (locale === "ar") return __ar.convo_new_message(inputs)
	if (locale === "as") return __as.convo_new_message(inputs)
	if (locale === "bn") return __bn.convo_new_message(inputs)
	if (locale === "de") return __de.convo_new_message(inputs)
	if (locale === "es") return __es.convo_new_message(inputs)
	if (locale === "fa") return __fa.convo_new_message(inputs)
	if (locale === "fr") return __fr.convo_new_message(inputs)
	if (locale === "gu") return __gu.convo_new_message(inputs)
	if (locale === "he") return __he.convo_new_message(inputs)
	if (locale === "hi") return __hi.convo_new_message(inputs)
	if (locale === "id") return __id.convo_new_message(inputs)
	if (locale === "ja") return __ja.convo_new_message(inputs)
	if (locale === "kn") return __kn.convo_new_message(inputs)
	if (locale === "ko") return __ko.convo_new_message(inputs)
	if (locale === "ku") return __ku.convo_new_message(inputs)
	if (locale === "ml") return __ml.convo_new_message(inputs)
	if (locale === "mr") return __mr.convo_new_message(inputs)
	if (locale === "ne") return __ne.convo_new_message(inputs)
	if (locale === "or") return __or.convo_new_message(inputs)
	if (locale === "pa") return __pa.convo_new_message(inputs)
	if (locale === "pt") return __pt.convo_new_message(inputs)
	if (locale === "ru") return __ru.convo_new_message(inputs)
	if (locale === "si") return __si.convo_new_message(inputs)
	if (locale === "ta") return __ta.convo_new_message(inputs)
	if (locale === "te") return __te.convo_new_message(inputs)
	if (locale === "th") return __th.convo_new_message(inputs)
	if (locale === "tr") return __tr.convo_new_message(inputs)
	if (locale === "ur") return __ur.convo_new_message(inputs)
	if (locale === "vi") return __vi.convo_new_message(inputs)
	return __zh_hans1.convo_new_message(inputs)
});
/**
* | output |
* | --- |
* | "No conversations yet" |
*
* @param {Convo_EmptyInputs} inputs
* @param {{ locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }} options
* @returns {LocalizedString}
*/
export const convo_empty = /** @type {((inputs?: Convo_EmptyInputs, options?: { locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }) => LocalizedString) & import('../runtime.js').MessageMetadata<Convo_EmptyInputs, { locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }, {}>} */ ((inputs = {}, options = {}) => {
	const locale = experimentalStaticLocale ?? options.locale ?? getLocale()
	if (locale === "en") return __en.convo_empty(inputs)
	if (locale === "ar") return __ar.convo_empty(inputs)
	if (locale === "as") return __as.convo_empty(inputs)
	if (locale === "bn") return __bn.convo_empty(inputs)
	if (locale === "de") return __de.convo_empty(inputs)
	if (locale === "es") return __es.convo_empty(inputs)
	if (locale === "fa") return __fa.convo_empty(inputs)
	if (locale === "fr") return __fr.convo_empty(inputs)
	if (locale === "gu") return __gu.convo_empty(inputs)
	if (locale === "he") return __he.convo_empty(inputs)
	if (locale === "hi") return __hi.convo_empty(inputs)
	if (locale === "id") return __id.convo_empty(inputs)
	if (locale === "ja") return __ja.convo_empty(inputs)
	if (locale === "kn") return __kn.convo_empty(inputs)
	if (locale === "ko") return __ko.convo_empty(inputs)
	if (locale === "ku") return __ku.convo_empty(inputs)
	if (locale === "ml") return __ml.convo_empty(inputs)
	if (locale === "mr") return __mr.convo_empty(inputs)
	if (locale === "ne") return __ne.convo_empty(inputs)
	if (locale === "or") return __or.convo_empty(inputs)
	if (locale === "pa") return __pa.convo_empty(inputs)
	if (locale === "pt") return __pt.convo_empty(inputs)
	if (locale === "ru") return __ru.convo_empty(inputs)
	if (locale === "si") return __si.convo_empty(inputs)
	if (locale === "ta") return __ta.convo_empty(inputs)
	if (locale === "te") return __te.convo_empty(inputs)
	if (locale === "th") return __th.convo_empty(inputs)
	if (locale === "tr") return __tr.convo_empty(inputs)
	if (locale === "ur") return __ur.convo_empty(inputs)
	if (locale === "vi") return __vi.convo_empty(inputs)
	return __zh_hans1.convo_empty(inputs)
});
/**
* | output |
* | --- |
* | "Loading..." |
*
* @param {Common_LoadingInputs} inputs
* @param {{ locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }} options
* @returns {LocalizedString}
*/
export const common_loading = /** @type {((inputs?: Common_LoadingInputs, options?: { locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }) => LocalizedString) & import('../runtime.js').MessageMetadata<Common_LoadingInputs, { locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }, {}>} */ ((inputs = {}, options = {}) => {
	const locale = experimentalStaticLocale ?? options.locale ?? getLocale()
	if (locale === "en") return __en.common_loading(inputs)
	if (locale === "ar") return __ar.common_loading(inputs)
	if (locale === "as") return __as.common_loading(inputs)
	if (locale === "bn") return __bn.common_loading(inputs)
	if (locale === "de") return __de.common_loading(inputs)
	if (locale === "es") return __es.common_loading(inputs)
	if (locale === "fa") return __fa.common_loading(inputs)
	if (locale === "fr") return __fr.common_loading(inputs)
	if (locale === "gu") return __gu.common_loading(inputs)
	if (locale === "he") return __he.common_loading(inputs)
	if (locale === "hi") return __hi.common_loading(inputs)
	if (locale === "id") return __id.common_loading(inputs)
	if (locale === "ja") return __ja.common_loading(inputs)
	if (locale === "kn") return __kn.common_loading(inputs)
	if (locale === "ko") return __ko.common_loading(inputs)
	if (locale === "ku") return __ku.common_loading(inputs)
	if (locale === "ml") return __ml.common_loading(inputs)
	if (locale === "mr") return __mr.common_loading(inputs)
	if (locale === "ne") return __ne.common_loading(inputs)
	if (locale === "or") return __or.common_loading(inputs)
	if (locale === "pa") return __pa.common_loading(inputs)
	if (locale === "pt") return __pt.common_loading(inputs)
	if (locale === "ru") return __ru.common_loading(inputs)
	if (locale === "si") return __si.common_loading(inputs)
	if (locale === "ta") return __ta.common_loading(inputs)
	if (locale === "te") return __te.common_loading(inputs)
	if (locale === "th") return __th.common_loading(inputs)
	if (locale === "tr") return __tr.common_loading(inputs)
	if (locale === "ur") return __ur.common_loading(inputs)
	if (locale === "vi") return __vi.common_loading(inputs)
	return __zh_hans1.common_loading(inputs)
});
/**
* | output |
* | --- |
* | "Something went wrong" |
*
* @param {Common_ErrorInputs} inputs
* @param {{ locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }} options
* @returns {LocalizedString}
*/
export const common_error = /** @type {((inputs?: Common_ErrorInputs, options?: { locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }) => LocalizedString) & import('../runtime.js').MessageMetadata<Common_ErrorInputs, { locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }, {}>} */ ((inputs = {}, options = {}) => {
	const locale = experimentalStaticLocale ?? options.locale ?? getLocale()
	if (locale === "en") return __en.common_error(inputs)
	if (locale === "ar") return __ar.common_error(inputs)
	if (locale === "as") return __as.common_error(inputs)
	if (locale === "bn") return __bn.common_error(inputs)
	if (locale === "de") return __de.common_error(inputs)
	if (locale === "es") return __es.common_error(inputs)
	if (locale === "fa") return __fa.common_error(inputs)
	if (locale === "fr") return __fr.common_error(inputs)
	if (locale === "gu") return __gu.common_error(inputs)
	if (locale === "he") return __he.common_error(inputs)
	if (locale === "hi") return __hi.common_error(inputs)
	if (locale === "id") return __id.common_error(inputs)
	if (locale === "ja") return __ja.common_error(inputs)
	if (locale === "kn") return __kn.common_error(inputs)
	if (locale === "ko") return __ko.common_error(inputs)
	if (locale === "ku") return __ku.common_error(inputs)
	if (locale === "ml") return __ml.common_error(inputs)
	if (locale === "mr") return __mr.common_error(inputs)
	if (locale === "ne") return __ne.common_error(inputs)
	if (locale === "or") return __or.common_error(inputs)
	if (locale === "pa") return __pa.common_error(inputs)
	if (locale === "pt") return __pt.common_error(inputs)
	if (locale === "ru") return __ru.common_error(inputs)
	if (locale === "si") return __si.common_error(inputs)
	if (locale === "ta") return __ta.common_error(inputs)
	if (locale === "te") return __te.common_error(inputs)
	if (locale === "th") return __th.common_error(inputs)
	if (locale === "tr") return __tr.common_error(inputs)
	if (locale === "ur") return __ur.common_error(inputs)
	if (locale === "vi") return __vi.common_error(inputs)
	return __zh_hans1.common_error(inputs)
});
/**
* | output |
* | --- |
* | "Retry" |
*
* @param {Common_RetryInputs} inputs
* @param {{ locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }} options
* @returns {LocalizedString}
*/
export const common_retry = /** @type {((inputs?: Common_RetryInputs, options?: { locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }) => LocalizedString) & import('../runtime.js').MessageMetadata<Common_RetryInputs, { locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }, {}>} */ ((inputs = {}, options = {}) => {
	const locale = experimentalStaticLocale ?? options.locale ?? getLocale()
	if (locale === "en") return __en.common_retry(inputs)
	if (locale === "ar") return __ar.common_retry(inputs)
	if (locale === "as") return __as.common_retry(inputs)
	if (locale === "bn") return __bn.common_retry(inputs)
	if (locale === "de") return __de.common_retry(inputs)
	if (locale === "es") return __es.common_retry(inputs)
	if (locale === "fa") return __fa.common_retry(inputs)
	if (locale === "fr") return __fr.common_retry(inputs)
	if (locale === "gu") return __gu.common_retry(inputs)
	if (locale === "he") return __he.common_retry(inputs)
	if (locale === "hi") return __hi.common_retry(inputs)
	if (locale === "id") return __id.common_retry(inputs)
	if (locale === "ja") return __ja.common_retry(inputs)
	if (locale === "kn") return __kn.common_retry(inputs)
	if (locale === "ko") return __ko.common_retry(inputs)
	if (locale === "ku") return __ku.common_retry(inputs)
	if (locale === "ml") return __ml.common_retry(inputs)
	if (locale === "mr") return __mr.common_retry(inputs)
	if (locale === "ne") return __ne.common_retry(inputs)
	if (locale === "or") return __or.common_retry(inputs)
	if (locale === "pa") return __pa.common_retry(inputs)
	if (locale === "pt") return __pt.common_retry(inputs)
	if (locale === "ru") return __ru.common_retry(inputs)
	if (locale === "si") return __si.common_retry(inputs)
	if (locale === "ta") return __ta.common_retry(inputs)
	if (locale === "te") return __te.common_retry(inputs)
	if (locale === "th") return __th.common_retry(inputs)
	if (locale === "tr") return __tr.common_retry(inputs)
	if (locale === "ur") return __ur.common_retry(inputs)
	if (locale === "vi") return __vi.common_retry(inputs)
	return __zh_hans1.common_retry(inputs)
});
/**
* | output |
* | --- |
* | "Save" |
*
* @param {Common_SaveInputs} inputs
* @param {{ locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }} options
* @returns {LocalizedString}
*/
export const common_save = /** @type {((inputs?: Common_SaveInputs, options?: { locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }) => LocalizedString) & import('../runtime.js').MessageMetadata<Common_SaveInputs, { locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }, {}>} */ ((inputs = {}, options = {}) => {
	const locale = experimentalStaticLocale ?? options.locale ?? getLocale()
	if (locale === "en") return __en.common_save(inputs)
	if (locale === "ar") return __ar.common_save(inputs)
	if (locale === "as") return __as.common_save(inputs)
	if (locale === "bn") return __bn.common_save(inputs)
	if (locale === "de") return __de.common_save(inputs)
	if (locale === "es") return __es.common_save(inputs)
	if (locale === "fa") return __fa.common_save(inputs)
	if (locale === "fr") return __fr.common_save(inputs)
	if (locale === "gu") return __gu.common_save(inputs)
	if (locale === "he") return __he.common_save(inputs)
	if (locale === "hi") return __hi.common_save(inputs)
	if (locale === "id") return __id.common_save(inputs)
	if (locale === "ja") return __ja.common_save(inputs)
	if (locale === "kn") return __kn.common_save(inputs)
	if (locale === "ko") return __ko.common_save(inputs)
	if (locale === "ku") return __ku.common_save(inputs)
	if (locale === "ml") return __ml.common_save(inputs)
	if (locale === "mr") return __mr.common_save(inputs)
	if (locale === "ne") return __ne.common_save(inputs)
	if (locale === "or") return __or.common_save(inputs)
	if (locale === "pa") return __pa.common_save(inputs)
	if (locale === "pt") return __pt.common_save(inputs)
	if (locale === "ru") return __ru.common_save(inputs)
	if (locale === "si") return __si.common_save(inputs)
	if (locale === "ta") return __ta.common_save(inputs)
	if (locale === "te") return __te.common_save(inputs)
	if (locale === "th") return __th.common_save(inputs)
	if (locale === "tr") return __tr.common_save(inputs)
	if (locale === "ur") return __ur.common_save(inputs)
	if (locale === "vi") return __vi.common_save(inputs)
	return __zh_hans1.common_save(inputs)
});
/**
* | output |
* | --- |
* | "Cancel" |
*
* @param {Common_CancelInputs} inputs
* @param {{ locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }} options
* @returns {LocalizedString}
*/
export const common_cancel = /** @type {((inputs?: Common_CancelInputs, options?: { locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }) => LocalizedString) & import('../runtime.js').MessageMetadata<Common_CancelInputs, { locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }, {}>} */ ((inputs = {}, options = {}) => {
	const locale = experimentalStaticLocale ?? options.locale ?? getLocale()
	if (locale === "en") return __en.common_cancel(inputs)
	if (locale === "ar") return __ar.common_cancel(inputs)
	if (locale === "as") return __as.common_cancel(inputs)
	if (locale === "bn") return __bn.common_cancel(inputs)
	if (locale === "de") return __de.common_cancel(inputs)
	if (locale === "es") return __es.common_cancel(inputs)
	if (locale === "fa") return __fa.common_cancel(inputs)
	if (locale === "fr") return __fr.common_cancel(inputs)
	if (locale === "gu") return __gu.common_cancel(inputs)
	if (locale === "he") return __he.common_cancel(inputs)
	if (locale === "hi") return __hi.common_cancel(inputs)
	if (locale === "id") return __id.common_cancel(inputs)
	if (locale === "ja") return __ja.common_cancel(inputs)
	if (locale === "kn") return __kn.common_cancel(inputs)
	if (locale === "ko") return __ko.common_cancel(inputs)
	if (locale === "ku") return __ku.common_cancel(inputs)
	if (locale === "ml") return __ml.common_cancel(inputs)
	if (locale === "mr") return __mr.common_cancel(inputs)
	if (locale === "ne") return __ne.common_cancel(inputs)
	if (locale === "or") return __or.common_cancel(inputs)
	if (locale === "pa") return __pa.common_cancel(inputs)
	if (locale === "pt") return __pt.common_cancel(inputs)
	if (locale === "ru") return __ru.common_cancel(inputs)
	if (locale === "si") return __si.common_cancel(inputs)
	if (locale === "ta") return __ta.common_cancel(inputs)
	if (locale === "te") return __te.common_cancel(inputs)
	if (locale === "th") return __th.common_cancel(inputs)
	if (locale === "tr") return __tr.common_cancel(inputs)
	if (locale === "ur") return __ur.common_cancel(inputs)
	if (locale === "vi") return __vi.common_cancel(inputs)
	return __zh_hans1.common_cancel(inputs)
});
/**
* | output |
* | --- |
* | "Delete" |
*
* @param {Common_DeleteInputs} inputs
* @param {{ locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }} options
* @returns {LocalizedString}
*/
export const common_delete = /** @type {((inputs?: Common_DeleteInputs, options?: { locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }) => LocalizedString) & import('../runtime.js').MessageMetadata<Common_DeleteInputs, { locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }, {}>} */ ((inputs = {}, options = {}) => {
	const locale = experimentalStaticLocale ?? options.locale ?? getLocale()
	if (locale === "en") return __en.common_delete(inputs)
	if (locale === "ar") return __ar.common_delete(inputs)
	if (locale === "as") return __as.common_delete(inputs)
	if (locale === "bn") return __bn.common_delete(inputs)
	if (locale === "de") return __de.common_delete(inputs)
	if (locale === "es") return __es.common_delete(inputs)
	if (locale === "fa") return __fa.common_delete(inputs)
	if (locale === "fr") return __fr.common_delete(inputs)
	if (locale === "gu") return __gu.common_delete(inputs)
	if (locale === "he") return __he.common_delete(inputs)
	if (locale === "hi") return __hi.common_delete(inputs)
	if (locale === "id") return __id.common_delete(inputs)
	if (locale === "ja") return __ja.common_delete(inputs)
	if (locale === "kn") return __kn.common_delete(inputs)
	if (locale === "ko") return __ko.common_delete(inputs)
	if (locale === "ku") return __ku.common_delete(inputs)
	if (locale === "ml") return __ml.common_delete(inputs)
	if (locale === "mr") return __mr.common_delete(inputs)
	if (locale === "ne") return __ne.common_delete(inputs)
	if (locale === "or") return __or.common_delete(inputs)
	if (locale === "pa") return __pa.common_delete(inputs)
	if (locale === "pt") return __pt.common_delete(inputs)
	if (locale === "ru") return __ru.common_delete(inputs)
	if (locale === "si") return __si.common_delete(inputs)
	if (locale === "ta") return __ta.common_delete(inputs)
	if (locale === "te") return __te.common_delete(inputs)
	if (locale === "th") return __th.common_delete(inputs)
	if (locale === "tr") return __tr.common_delete(inputs)
	if (locale === "ur") return __ur.common_delete(inputs)
	if (locale === "vi") return __vi.common_delete(inputs)
	return __zh_hans1.common_delete(inputs)
});
/**
* | output |
* | --- |
* | "Confirm" |
*
* @param {Common_ConfirmInputs} inputs
* @param {{ locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }} options
* @returns {LocalizedString}
*/
export const common_confirm = /** @type {((inputs?: Common_ConfirmInputs, options?: { locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }) => LocalizedString) & import('../runtime.js').MessageMetadata<Common_ConfirmInputs, { locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }, {}>} */ ((inputs = {}, options = {}) => {
	const locale = experimentalStaticLocale ?? options.locale ?? getLocale()
	if (locale === "en") return __en.common_confirm(inputs)
	if (locale === "ar") return __ar.common_confirm(inputs)
	if (locale === "as") return __as.common_confirm(inputs)
	if (locale === "bn") return __bn.common_confirm(inputs)
	if (locale === "de") return __de.common_confirm(inputs)
	if (locale === "es") return __es.common_confirm(inputs)
	if (locale === "fa") return __fa.common_confirm(inputs)
	if (locale === "fr") return __fr.common_confirm(inputs)
	if (locale === "gu") return __gu.common_confirm(inputs)
	if (locale === "he") return __he.common_confirm(inputs)
	if (locale === "hi") return __hi.common_confirm(inputs)
	if (locale === "id") return __id.common_confirm(inputs)
	if (locale === "ja") return __ja.common_confirm(inputs)
	if (locale === "kn") return __kn.common_confirm(inputs)
	if (locale === "ko") return __ko.common_confirm(inputs)
	if (locale === "ku") return __ku.common_confirm(inputs)
	if (locale === "ml") return __ml.common_confirm(inputs)
	if (locale === "mr") return __mr.common_confirm(inputs)
	if (locale === "ne") return __ne.common_confirm(inputs)
	if (locale === "or") return __or.common_confirm(inputs)
	if (locale === "pa") return __pa.common_confirm(inputs)
	if (locale === "pt") return __pt.common_confirm(inputs)
	if (locale === "ru") return __ru.common_confirm(inputs)
	if (locale === "si") return __si.common_confirm(inputs)
	if (locale === "ta") return __ta.common_confirm(inputs)
	if (locale === "te") return __te.common_confirm(inputs)
	if (locale === "th") return __th.common_confirm(inputs)
	if (locale === "tr") return __tr.common_confirm(inputs)
	if (locale === "ur") return __ur.common_confirm(inputs)
	if (locale === "vi") return __vi.common_confirm(inputs)
	return __zh_hans1.common_confirm(inputs)
});
/**
* | output |
* | --- |
* | "Back" |
*
* @param {Common_BackInputs} inputs
* @param {{ locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }} options
* @returns {LocalizedString}
*/
export const common_back = /** @type {((inputs?: Common_BackInputs, options?: { locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }) => LocalizedString) & import('../runtime.js').MessageMetadata<Common_BackInputs, { locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }, {}>} */ ((inputs = {}, options = {}) => {
	const locale = experimentalStaticLocale ?? options.locale ?? getLocale()
	if (locale === "en") return __en.common_back(inputs)
	if (locale === "ar") return __ar.common_back(inputs)
	if (locale === "as") return __as.common_back(inputs)
	if (locale === "bn") return __bn.common_back(inputs)
	if (locale === "de") return __de.common_back(inputs)
	if (locale === "es") return __es.common_back(inputs)
	if (locale === "fa") return __fa.common_back(inputs)
	if (locale === "fr") return __fr.common_back(inputs)
	if (locale === "gu") return __gu.common_back(inputs)
	if (locale === "he") return __he.common_back(inputs)
	if (locale === "hi") return __hi.common_back(inputs)
	if (locale === "id") return __id.common_back(inputs)
	if (locale === "ja") return __ja.common_back(inputs)
	if (locale === "kn") return __kn.common_back(inputs)
	if (locale === "ko") return __ko.common_back(inputs)
	if (locale === "ku") return __ku.common_back(inputs)
	if (locale === "ml") return __ml.common_back(inputs)
	if (locale === "mr") return __mr.common_back(inputs)
	if (locale === "ne") return __ne.common_back(inputs)
	if (locale === "or") return __or.common_back(inputs)
	if (locale === "pa") return __pa.common_back(inputs)
	if (locale === "pt") return __pt.common_back(inputs)
	if (locale === "ru") return __ru.common_back(inputs)
	if (locale === "si") return __si.common_back(inputs)
	if (locale === "ta") return __ta.common_back(inputs)
	if (locale === "te") return __te.common_back(inputs)
	if (locale === "th") return __th.common_back(inputs)
	if (locale === "tr") return __tr.common_back(inputs)
	if (locale === "ur") return __ur.common_back(inputs)
	if (locale === "vi") return __vi.common_back(inputs)
	return __zh_hans1.common_back(inputs)
});
/**
* | output |
* | --- |
* | "Close" |
*
* @param {Common_CloseInputs} inputs
* @param {{ locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }} options
* @returns {LocalizedString}
*/
export const common_close = /** @type {((inputs?: Common_CloseInputs, options?: { locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }) => LocalizedString) & import('../runtime.js').MessageMetadata<Common_CloseInputs, { locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }, {}>} */ ((inputs = {}, options = {}) => {
	const locale = experimentalStaticLocale ?? options.locale ?? getLocale()
	if (locale === "en") return __en.common_close(inputs)
	if (locale === "ar") return __ar.common_close(inputs)
	if (locale === "as") return __as.common_close(inputs)
	if (locale === "bn") return __bn.common_close(inputs)
	if (locale === "de") return __de.common_close(inputs)
	if (locale === "es") return __es.common_close(inputs)
	if (locale === "fa") return __fa.common_close(inputs)
	if (locale === "fr") return __fr.common_close(inputs)
	if (locale === "gu") return __gu.common_close(inputs)
	if (locale === "he") return __he.common_close(inputs)
	if (locale === "hi") return __hi.common_close(inputs)
	if (locale === "id") return __id.common_close(inputs)
	if (locale === "ja") return __ja.common_close(inputs)
	if (locale === "kn") return __kn.common_close(inputs)
	if (locale === "ko") return __ko.common_close(inputs)
	if (locale === "ku") return __ku.common_close(inputs)
	if (locale === "ml") return __ml.common_close(inputs)
	if (locale === "mr") return __mr.common_close(inputs)
	if (locale === "ne") return __ne.common_close(inputs)
	if (locale === "or") return __or.common_close(inputs)
	if (locale === "pa") return __pa.common_close(inputs)
	if (locale === "pt") return __pt.common_close(inputs)
	if (locale === "ru") return __ru.common_close(inputs)
	if (locale === "si") return __si.common_close(inputs)
	if (locale === "ta") return __ta.common_close(inputs)
	if (locale === "te") return __te.common_close(inputs)
	if (locale === "th") return __th.common_close(inputs)
	if (locale === "tr") return __tr.common_close(inputs)
	if (locale === "ur") return __ur.common_close(inputs)
	if (locale === "vi") return __vi.common_close(inputs)
	return __zh_hans1.common_close(inputs)
});
/**
* | output |
* | --- |
* | "{count} views" |
*
* @param {Common_ViewsInputs} inputs
* @param {{ locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }} options
* @returns {LocalizedString}
*/
export const common_views = /** @type {((inputs: Common_ViewsInputs, options?: { locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }) => LocalizedString) & import('../runtime.js').MessageMetadata<Common_ViewsInputs, { locale?: "en" | "ar" | "as" | "bn" | "de" | "es" | "fa" | "fr" | "gu" | "he" | "hi" | "id" | "ja" | "kn" | "ko" | "ku" | "ml" | "mr" | "ne" | "or" | "pa" | "pt" | "ru" | "si" | "ta" | "te" | "th" | "tr" | "ur" | "vi" | "zh-Hans" }, {}>} */ ((inputs, options = {}) => {
	const locale = experimentalStaticLocale ?? options.locale ?? getLocale()
	if (locale === "en") return __en.common_views(inputs)
	if (locale === "ar") return __ar.common_views(inputs)
	if (locale === "as") return __as.common_views(inputs)
	if (locale === "bn") return __bn.common_views(inputs)
	if (locale === "de") return __de.common_views(inputs)
	if (locale === "es") return __es.common_views(inputs)
	if (locale === "fa") return __fa.common_views(inputs)
	if (locale === "fr") return __fr.common_views(inputs)
	if (locale === "gu") return __gu.common_views(inputs)
	if (locale === "he") return __he.common_views(inputs)
	if (locale === "hi") return __hi.common_views(inputs)
	if (locale === "id") return __id.common_views(inputs)
	if (locale === "ja") return __ja.common_views(inputs)
	if (locale === "kn") return __kn.common_views(inputs)
	if (locale === "ko") return __ko.common_views(inputs)
	if (locale === "ku") return __ku.common_views(inputs)
	if (locale === "ml") return __ml.common_views(inputs)
	if (locale === "mr") return __mr.common_views(inputs)
	if (locale === "ne") return __ne.common_views(inputs)
	if (locale === "or") return __or.common_views(inputs)
	if (locale === "pa") return __pa.common_views(inputs)
	if (locale === "pt") return __pt.common_views(inputs)
	if (locale === "ru") return __ru.common_views(inputs)
	if (locale === "si") return __si.common_views(inputs)
	if (locale === "ta") return __ta.common_views(inputs)
	if (locale === "te") return __te.common_views(inputs)
	if (locale === "th") return __th.common_views(inputs)
	if (locale === "tr") return __tr.common_views(inputs)
	if (locale === "ur") return __ur.common_views(inputs)
	if (locale === "vi") return __vi.common_views(inputs)
	return __zh_hans1.common_views(inputs)
});

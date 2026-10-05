# Integration to Input Evaluation Interface Requirements

**Status:** Draft for Gate 1 discussion  
**Interface:** Integration -> Input Evaluation  
**Purpose:** Define the minimum information and representation that Input Evaluation needs to assess GitHub bug report quality consistently.

## 1. Responsibility Boundary

The two subsystems have different responsibilities:

- **Integration** retrieves, preserves, and structures the information contained in a GitHub issue.
- **Input Evaluation** determines whether that information is complete, clear, and sufficient under criteria C1-C7.

Integration should not infer missing information, improve unclear descriptions, or make report-quality judgments. Input Evaluation must receive the reporter's original wording so that it can make those judgments independently.

## 2. Recommended Approach

Input Evaluation recommends a simplified **layered/hybrid approach** for Gate 1. The interface should provide both:

1. The original GitHub issue content and source metadata.
2. A structured representation of fields or sections extracted from the issue.

Keeping both representations allows Input Evaluation to use a stable structure while retaining the ability to verify parsing and mapping decisions against the original report.

## 3. Minimum Input Data

Each report passed to Input Evaluation should include:

| Field | Requirement | Purpose |
|---|---|---|
| Repository | Required | Identifies the source project. |
| Issue number | Required | Identifies the report within the repository. |
| Issue URL | Required | Provides traceability to the original report. |
| Issue title | Required | Preserves the original summary. |
| Raw Markdown body | Required | Preserves the reporter's complete original wording and formatting. |
| Labels | Required, empty list allowed | Preserves project-provided classification. |
| Created time | Required | Preserves source context. |
| Updated time | Required | Indicates whether the report changed after creation. |
| Structured sections | Required when identifiable, empty list allowed | Provides a stable representation of template fields or body sections. |

## 4. Extracted Section Data

For every identified field or section, Integration should preserve:

| Field | Requirement |
|---|---|
| `field_id` | Include when available from an Issue Form or template. |
| `original_label` | Preserve the project's original heading or field label. |
| `value` | Preserve the reporter's original content without rewriting it. |
| `required` | Include when the repository template defines the field as required or optional. |
| `status` | Distinguish a supplied value, a blank field, and a field absent from the report. |

## 5. Proposed Data Structure

```json
{
  "repository": "owner/project",
  "issue_number": 123,
  "issue_url": "https://github.com/owner/project/issues/123",
  "title": "Application crashes after clicking Save",
  "raw_body": "...original Markdown...",
  "labels": ["bug"],
  "created_at": "2026-09-30T14:00:00Z",
  "updated_at": "2026-09-30T16:30:00Z",
  "sections": [
    {
      "field_id": "what-happened",
      "original_label": "What happened?",
      "required": true,
      "status": "provided",
      "value": "Application crashes after clicking Save."
    },
    {
      "field_id": "version",
      "original_label": "Version",
      "required": true,
      "status": "provided",
      "value": "2.3.1"
    }
  ]
}
```

## 6. Free-Form and Missing Information

- Free-form issues remain valid inputs even when no template fields can be identified.
- For a free-form issue, Integration should provide the title, raw body, source metadata, and an empty `sections` list if no reliable sections can be extracted.
- Missing information must be represented explicitly rather than inferred or generated.
- The interface should distinguish between:
  - a field that contains a value;
  - a field that appears in the report but is blank; and
  - a field that does not appear in the report.
- Input Evaluation will determine whether an absent item is missing information or is not applicable to that report.

## 7. Semantic Mapping

Integration may optionally map project-specific labels such as `What happened?` or `Current behavior` to universal concepts such as `observed_behavior`.

If semantic mapping is provided:

- the original label and content must remain available;
- the mapping must be traceable to the original field;
- the mapped concept should be presented as Integration's representation, not as a quality judgment; and
- Input Evaluation must be able to evaluate the original content if the mapping is uncertain or incorrect.

## 8. Support for Input Evaluation Criteria

The proposed interface supports assessment of:

| Criterion | Assessment focus |
|---|---|
| C1 | Bug description |
| C2 | Steps to reproduce |
| C3 | Expected behavior |
| C4 | Observed behavior |
| C5 | Environment and version |
| C6 | Supporting evidence |
| C7 | Clarity and specificity |

Integration supplies the report content and its representation. Input Evaluation applies these criteria and produces the report-quality assessment.

## 9. Proposed Minimum Interface Agreement

> Input Evaluation receives the original GitHub issue content, source metadata, and a structured representation of any identified fields. Integration preserves the reporter's original wording and explicitly represents missing or blank information. Input Evaluation remains responsible for interpreting the content and evaluating report quality.

## 10. Items to Confirm with Integration

Before finalizing the Gate 1 interface agreement, the teams should confirm:

1. Whether Integration can provide both raw Markdown and structured sections.
2. Which source metadata fields are available in the first implementation.
3. How blank, absent, and unrecognized fields will be encoded.
4. Whether Issue Form field identifiers and required/optional status can be preserved.
5. Whether semantic mappings will be included at Gate 1 or deferred.
6. How the interface will handle parsing errors and unsupported templates.

The repository installation mechanism involves Integration and the broader system architecture. Input Evaluation can review any installation decision that changes the information available through this interface.

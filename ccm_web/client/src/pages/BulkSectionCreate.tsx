import React, { useEffect, useState } from 'react'
import { styled } from '@mui/material/styles'
import { Backdrop, Button, CircularProgress, Grid, Typography } from '@mui/material'

import { addCourseSections, getCourseSections } from '../api.js'
import APIErrorMessage from '../components/APIErrorMessage.js'
import BulkApiErrorContent from '../components/BulkApiErrorContent.js'
import BulkSectionCreateUploadConfirmationTable, { Section } from '../components/BulkSectionCreateUploadConfirmationTable.js'
import {
  DuplicateSectionInFileSectionRowsValidator, SectionNameLengthValidator,
  SectionRowsValidator, SectionsRowInvalidation
} from '../components/BulkSectionCreateValidators.js'
import CanvasSettingsLink from '../components/CanvasSettingsLink.js'
import ConfirmDialog from '../components/ConfirmDialog.js'
import CSVFileName from '../components/CSVFileName.js'
import ErrorAlert from '../components/ErrorAlert.js'
import ExampleFileDownloadHeader, { ExampleFileDownloadHeaderProps } from '../components/ExampleFileDownloadHeader.js'
import FileUpload from '../components/FileUpload.js'
import Help from '../components/Help.js'
import RowLevelErrorsContent from '../components/RowLevelErrorsContent.js'
import SuccessCard from '../components/SuccessCard.js'
import ValidationErrorTable from '../components/ValidationErrorTable.js'
import usePromise from '../hooks/usePromise.js'
import { CanvasCourseSection } from '../models/canvas.js'
import { CCMComponentProps } from '../models/FeatureUIData.js'
import { InvalidationType } from '../models/models.js'
import CSVSchemaValidator, { SchemaInvalidation } from '../utils/CSVSchemaValidator.js'
import FileParserWrapper, { CSVRecord } from '../utils/FileParserWrapper.js'
import { getRowNumber } from '../utils/fileUtils.js'

const PREFIX = 'BulkSectionCreate'

const classes = {
  root: `${PREFIX}-root`,
  confirmContainer: `${PREFIX}-confirmContainer`,
  uploadContainer: `${PREFIX}-uploadContainer`,
  backdrop: `${PREFIX}-backdrop`,
  popover: `${PREFIX}-popover`,
  paper: `${PREFIX}-paper`,
  table: `${PREFIX}-table`,
  buttonGroup: `${PREFIX}-buttonGroup`
}

const Root = styled('div')((
  {
    theme
  }
) => ({
  [`&.${classes.root}`]: {
    textAlign: 'left'
  },

  [`& .${classes.confirmContainer}`]: {
    position: 'relative',
    zIndex: 0,
    textAlign: 'center'
  },

  [`&.${classes.uploadContainer}`]: {
    position: 'relative',
    zIndex: 0,
    textAlign: 'center'
  },

  [`& .${classes.backdrop}`]: {
    zIndex: theme.zIndex.drawer + 1,
    color: '#fff',
    position: 'absolute'
  },

  [`& .${classes.popover}`]: {
    pointerEvents: 'none'
  },

  [`& .${classes.paper}`]: {
    padding: theme.spacing(1)
  },

  [`& .${classes.table}`]: {
    paddingLeft: 10,
    paddingRight: 10
  },

  [`& .${classes.buttonGroup}`]: {
    marginTop: theme.spacing(1)
  }
}))

interface SectionNameRecord extends CSVRecord {
  SECTION_NAME: string
}

const isSectionNameRecord = (r: CSVRecord): r is SectionNameRecord => {
  return typeof r.SECTION_NAME === 'string'
}

enum BulkSectionCreatePageState {
  UploadPending,
  LoadingExistingSectionNamesFailed,
  InvalidUpload,
  Submit,
  CreateSectionsSuccess,
  CreateSectionsError,
  Saving
}

interface BulkSectionCreatePageStateData {
  state: BulkSectionCreatePageState
  rowInvalidations: SectionsRowInvalidation[]
  schemaInvalidations: SchemaInvalidation[]
}

function BulkSectionCreate (props: CCMComponentProps): JSX.Element {
  const [pageState, setPageState] = useState<BulkSectionCreatePageStateData>(
    { state: BulkSectionCreatePageState.UploadPending, schemaInvalidations: [], rowInvalidations: [] }
  )
  const [file, setFile] = useState<File|undefined>(undefined)
  const [sectionNames, setSectionNames] = useState<string[]>([])
  const [existingSectionNames, setExistingSectionNames] = useState<string[]|undefined>(undefined)

  const [doGetSections, isGetSectionsLoading, getSectionsError] = usePromise(
    async () => await getCourseSections(props.globals.course.id),
    (value: CanvasCourseSection[]) => {
      const existingSuggestions = value.map(s => { return s.name.toUpperCase() })
      setExistingSectionNames(existingSuggestions)
    }
  )

  const [doAddSections, isAddSectionsLoading, addSectionsError] = usePromise(
    async () => await addCourseSections(props.globals.course.id, sectionNames, props.csrfToken.token),
    (newSections: CanvasCourseSection[]) => {
      const originalSectionNames: string[] = (existingSectionNames != null) ? existingSectionNames : []
      setPageState({ state: BulkSectionCreatePageState.CreateSectionsSuccess, schemaInvalidations: [], rowInvalidations: [] })
      setExistingSectionNames([...new Set([...originalSectionNames, ...newSections.map(newSection => { return newSection.name.toUpperCase() })])])
    }
  )

  useEffect(() => {
    if (getSectionsError !== undefined) {
      setPageState({ state: BulkSectionCreatePageState.LoadingExistingSectionNamesFailed, schemaInvalidations: [], rowInvalidations: [] })
    }
  }, [getSectionsError])

  useEffect(() => {
    if (pageState.state === BulkSectionCreatePageState.Saving) {
      const serverInvalidations = doServerValidation()
      if (serverInvalidations.length !== 0) {
        handleRowLevelInvalidationError(serverInvalidations)
      } else {
        void doAddSections()
      }
    }
  }, [existingSectionNames])

  const isSubmitting = (): boolean => {
    return (isGetSectionsLoading || isAddSectionsLoading)
  }

  const submit = async (): Promise<void> => {
    setPageState({ state: BulkSectionCreatePageState.Saving, schemaInvalidations: [], rowInvalidations: [] })
    void doGetSections()
  }

  useEffect(() => {
    if (addSectionsError !== undefined) {
      setPageState({ state: BulkSectionCreatePageState.CreateSectionsError, schemaInvalidations: [], rowInvalidations: [] })
    }
  }, [addSectionsError])

  class DuplicateExistingSectionRowsValidator implements SectionRowsValidator {
    validate = (sectionNames: string[]): SectionsRowInvalidation[] => {
      const sortedSectionNames = sectionNames.map(n => { return n.toUpperCase() }).sort((a, b) => { return a.localeCompare(b) })
      const duplicates: string[] = []
      for (let i = 0; i < sortedSectionNames.length; ++i) {
        if ((existingSectionNames?.includes(sortedSectionNames[i])) ?? false) {
          duplicates.push(sortedSectionNames[i])
        }
      }

      const invalidations: SectionsRowInvalidation[] = []
      sectionNames.forEach((sectionName, i) => {
        if (duplicates.includes(sectionName.toUpperCase())) {
          invalidations.push({
            message: 'Section name already used in this course: "' + sectionName + '"',
            rowNumber: getRowNumber(i),
            type: InvalidationType.Error
          })
        }
      })

      return invalidations
    }
  }

  useEffect(() => {
    if (sectionNames.length > 0) {
      const clientInvalidations = doClientValidation()
      if (clientInvalidations.length !== 0) {
        handleRowLevelInvalidationError(clientInvalidations)
      } else {
        setPageState({ state: BulkSectionCreatePageState.Submit, schemaInvalidations: [], rowInvalidations: [] })
      }
    }
  }, [sectionNames])

  const resetPageState = (): void => {
    setPageState({ state: BulkSectionCreatePageState.UploadPending, schemaInvalidations: [], rowInvalidations: [] })
  }

  const handleSchemaError = (schemaInvalidations: SchemaInvalidation[]): void => {
    setPageState({ state: BulkSectionCreatePageState.InvalidUpload, schemaInvalidations: schemaInvalidations, rowInvalidations: [] })
  }

  const handleRowLevelInvalidationError = (invalidations: SectionsRowInvalidation[]): void => {
    setPageState({ state: BulkSectionCreatePageState.InvalidUpload, schemaInvalidations: [], rowInvalidations: invalidations })
  }

  const handleParseSuccess = (sectionNames: string[]): void => {
    setSectionNames(sectionNames)
    setPageState({ state: BulkSectionCreatePageState.Submit, schemaInvalidations: [], rowInvalidations: [] })
  }

  const handleParseComplete = (headers: string[] | undefined, data: CSVRecord[]): void => {
    const csvValidator = new CSVSchemaValidator<SectionNameRecord>(['SECTION_NAME'], isSectionNameRecord, 60)
    const validationResult = csvValidator.validate(headers, data)
    if (!validationResult.valid) return handleSchemaError(validationResult.schemaInvalidations)

    const sectionNames = validationResult.validData.map(r => r.SECTION_NAME)
    return handleParseSuccess(sectionNames)
  }

  const parseFile = (file: File): void => {
    const parser = new FileParserWrapper()
    parser.parseCSV(
      file,
      handleParseComplete,
      (message) => handleSchemaError([{ message, type: InvalidationType.Error }])
    )
  }

  useEffect(() => {
    if (file !== undefined) {
      parseFile(file)
    }
  }, [file])

  const doClientValidation = (): SectionsRowInvalidation[] => {
    const rowInvalidations: SectionsRowInvalidation[] = []

    const duplicateNamesInFileValidator: SectionRowsValidator = new DuplicateSectionInFileSectionRowsValidator()
    rowInvalidations.push(...duplicateNamesInFileValidator.validate(sectionNames))
    const sectionNamesLengthValidator = new SectionNameLengthValidator()
    rowInvalidations.push(...sectionNamesLengthValidator.validate(sectionNames))

    return rowInvalidations
  }

  const doServerValidation = (): SectionsRowInvalidation[] => {
    const rowInvalidations: SectionsRowInvalidation[] = []
    const duplicatesNamesInCanvasValidator: DuplicateExistingSectionRowsValidator = new DuplicateExistingSectionRowsValidator()
    rowInvalidations.push(...duplicatesNamesInCanvasValidator.validate(sectionNames))

    return rowInvalidations
  }

  const renderUploadHeader = (): JSX.Element => {
    const fileData =
`SECTION_NAME
Section 001`
    const fileDownloadHeaderProps: ExampleFileDownloadHeaderProps = {
      body: <Typography>Your file should include one section name per line.</Typography>,
      fileData: fileData,
      fileName: 'sections.csv'
    }
    return <ExampleFileDownloadHeader {...fileDownloadHeaderProps} />
  }

  const renderLoadingText = (): JSX.Element | undefined => {
    if (isGetSectionsLoading) {
      return (<Typography>Loading Section Information</Typography>)
    } else if (isAddSectionsLoading) {
      return (<Typography>Saving Section Information</Typography>)
    }
  }

  const renderFileUpload = (): JSX.Element => {
    return (
      <Root className={classes.uploadContainer}>
        <Grid container>
          <Grid item xs={12}>
            <FileUpload onUploadComplete={(file) => setFile(file)} />
          </Grid>
        </Grid>
        <Backdrop className={classes.backdrop} open={isGetSectionsLoading}>
          <Grid container>
            <Grid item xs={12}>
              <CircularProgress color="inherit" />
            </Grid>
            <Grid item xs={12}>
            {renderLoadingText()}
            </Grid>
          </Grid>
        </Backdrop>
      </Root>
    )
  }

  const renderUpload = (): JSX.Element => {
    return (
      <div>
        {renderUploadHeader()}
        {renderFileUpload()}
      </div>
    )
  }

  const renderTopLevelErrors = (errors: JSX.Element[]): JSX.Element => {
    return (
      <div>
        {file !== undefined && <CSVFileName file={file} />}
        <ErrorAlert messages={errors} tryAgain={resetPageState} />
      </div>
    )
  }

  const renderInvalidUpload = (): JSX.Element => {
    let rowLevelErrors: JSX.Element | undefined
    let schemaLevelErrors: JSX.Element | undefined
    if (pageState.rowInvalidations.length > 0) {
      rowLevelErrors = (
        <>
        {file !== undefined && <CSVFileName file={file} />}
        <RowLevelErrorsContent
          table={<ValidationErrorTable invalidations={pageState.rowInvalidations} />}
          resetUpload={resetPageState}
          title='Review your CSV file'
        />
        </>
      )
    }
    if (pageState.schemaInvalidations.length > 0) {
      const schemaErrors: JSX.Element[] = pageState.schemaInvalidations.map((invalidation, i) => {
        return <Typography key={i}>{invalidation.message}</Typography>
      })
      schemaLevelErrors = <div>{renderTopLevelErrors(schemaErrors)}</div>
    }
    return (
      <div>
        {schemaLevelErrors !== undefined && schemaLevelErrors}
        {rowLevelErrors !== undefined && rowLevelErrors}
      </div>
    )
  }

  const renderConfirm = (sectionNames: Section[]): JSX.Element => {
    return (
      <div className={classes.confirmContainer}>
        {file !== undefined && <CSVFileName file={file} />}
        <Grid container>
          <Grid item xs={12} sm={9} sx={{ order: { xs: 2, sm: 1 } }} className={classes.table}>
            <BulkSectionCreateUploadConfirmationTable sectionNames={sectionNames} />
          </Grid>
          <Grid item xs={12} sm={3} sx={{ order: { xs: 1, sm: 2 } }}>
            <ConfirmDialog submit={submit} cancel={resetPageState} disabled={isSubmitting()} />
          </Grid>
        </Grid>
        <Backdrop className={classes.backdrop} open={isAddSectionsLoading}>
        <Grid container>
          <Grid item xs={12}>
            <CircularProgress color="inherit" />
          </Grid>
          <Grid item xs={12}>
          {renderLoadingText()}
          </Grid>
        </Grid>
      </Backdrop>
      </div>)
  }

  const sectionNamesToSection = (sectionNames: string[]): Section[] => {
    return sectionNames.map((name, i) => ({ rowNumber: getRowNumber(i), sectionName: name }))
  }

  const renderSuccess = (): JSX.Element => {
    const { canvasURL, course } = props.globals
    const settingsURL = `${canvasURL}/courses/${course.id}/settings`
    const message = <Typography>New sections have been added!</Typography>
    const nextAction = (
      <span>
        See your sections on the <CanvasSettingsLink url={settingsURL} /> for your course.
      </span>
    )
    return (
      <>
      <SuccessCard {...{ message, nextAction }} />
      <Grid container className={classes.buttonGroup} justifyContent='flex-start'>
        <Button variant='outlined' aria-label={`Start ${props.title} again`} onClick={resetPageState}>
          Start Again
        </Button>
      </Grid>
      </>
    )
  }

  const renderComponent = (): JSX.Element | undefined => {
    switch (pageState.state) {
      case BulkSectionCreatePageState.UploadPending:
        return renderUpload()
      case BulkSectionCreatePageState.LoadingExistingSectionNamesFailed:
        return (
          <ErrorAlert
            messages={[<APIErrorMessage key={0} context='loading section data' error={getSectionsError} />]}
            tryAgain={resetPageState}
          />
        )
      case BulkSectionCreatePageState.InvalidUpload:
        return renderInvalidUpload()
      case BulkSectionCreatePageState.Submit:
      case BulkSectionCreatePageState.Saving:
        return renderConfirm(sectionNamesToSection(sectionNames))
      case BulkSectionCreatePageState.CreateSectionsSuccess:
        return renderSuccess()
      case BulkSectionCreatePageState.CreateSectionsError:
        if (addSectionsError !== undefined) {
          return <BulkApiErrorContent error={addSectionsError} file={file} tryAgain={resetPageState} />
        }
        return
      default:
        return <div>?</div>
    }
  }

  return (
    <Root className={classes.root}>
      <Help baseHelpURL={props.globals.baseHelpURL} helpURLEnding={props.helpURLEnding} />
      <Typography variant='h5' component='h1'>{props.title}</Typography>
      {renderComponent()}
    </Root>
  )
}

export default BulkSectionCreate

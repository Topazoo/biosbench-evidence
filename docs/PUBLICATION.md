# Publication status and remaining steps

Peter Swanson confirmed authority over the included project components and
authorized MIT licensing and public GitHub publication on 2026-10-14. The root
LICENSE is the effective MIT license. The former proposal notice was removed.

The local source is prepared for publication; no remote has been created or
pushed by this task. Remaining steps:

1. Obtain the verified existing authenticated GitHub route and resolve the
   destination account/repository. Access is currently blocked; no credentials,
   tokens, grants, or duplicate authentication setup should be created here.
2. Review the exact commit/archive intended for release. Keep the private audit
   and approval records outside the repository. Local checks cover the explicit
   33-file source allowlist, privacy patterns, and synthetic fixture reproduction.
3. Execute the configured Linux/Windows CI matrix with Python 3.12.14 when GitHub
   access is available. Local Windows execution does not prove Linux or hosted
   CI results. Establish a private security-reporting contact before launch.
4. Present a concrete repository/branch-protection proposal with the actual
   repository, branch, check names, review rules, bypass permissions, and any
   account-plan limitations. Obtain action-time approval before changing these
   security settings; none have been changed or preapproved by this task.
5. Publish the reviewed version through the verified route, then verify remote
   visibility, the exact pushed commit, CI results, and approved protections.

The first release intentionally supports a narrower portable API than the
engineering application. Flash-survey payload structure and board extensions
remain unsupported; this limitation is documented rather than a licensing block.
No firmware-safety, full semantic-compatibility, or physical-validation claim is
made. Ongoing engineering workspaces are outside the publication workflow.

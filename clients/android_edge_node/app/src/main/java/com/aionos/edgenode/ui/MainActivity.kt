package com.aionos.edgenode.ui

import android.content.ComponentName
import android.content.Intent
import android.content.ServiceConnection
import android.content.pm.PackageManager
import android.graphics.Color
import android.graphics.Typeface
import android.os.Build
import android.os.Bundle
import android.os.IBinder
import android.text.InputType
import android.util.TypedValue
import android.view.Gravity
import android.view.View
import android.widget.Button
import android.widget.EditText
import android.widget.LinearLayout
import android.widget.ProgressBar
import android.widget.ScrollView
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity
import androidx.cardview.widget.CardView
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.lifecycleScope
import androidx.lifecycle.repeatOnLifecycle
import androidx.core.graphics.toColorInt
import com.aionos.edgenode.R
import com.aionos.edgenode.model.PoStState
import com.aionos.edgenode.model.PoStStatus
import com.aionos.edgenode.service.PoStDaemonService
import com.aionos.edgenode.identity.WalletManager
import com.aionos.edgenode.network.NetworkManager
import kotlinx.coroutines.Job
import kotlinx.coroutines.launch
import java.util.Locale

/**
 * Main Activity UI binding to [PoStDaemonService], displaying node status,
 * RAM allocation controls, real-time hardware metrics, and proof status.
 */
class MainActivity : AppCompatActivity() {

    private var daemonService: PoStDaemonService? = null
    private var isBound = false
    private var observationJob: Job? = null
    private val walletManager = WalletManager()
    private val networkManager = NetworkManager()

    private lateinit var tvStatus: TextView
    private lateinit var etRam: EditText
    private lateinit var etIterations: EditText
    private lateinit var btnStart: Button
    private lateinit var btnPauseResume: Button
    private lateinit var btnCancel: Button
    private lateinit var progressBar: ProgressBar
    private lateinit var tvAllocatedRam: TextView
    private lateinit var tvHashes: TextView
    private lateinit var tvExecutionTime: TextView
    private lateinit var tvHashRate: TextView
    private lateinit var tvProofDigest: TextView
    private lateinit var tvErrorMessage: TextView
    
    // New UI Elements
    private lateinit var tvAionId: TextView
    private lateinit var tvBalance: TextView
    private lateinit var tvPeers: TextView

    private val serviceConnection = object : ServiceConnection {
        override fun onServiceConnected(name: ComponentName?, binder: IBinder?) {
            val localBinder = binder as? PoStDaemonService.LocalBinder
            daemonService = localBinder?.getService()
            isBound = true
            observeDaemonState()
        }

        override fun onServiceDisconnected(name: ComponentName?) {
            daemonService = null
            isBound = false
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        buildUiLayout()
        requestNotificationPermissionIfNeeded()
    }

    override fun onStart() {
        super.onStart()
        val intent = Intent(this, PoStDaemonService::class.java)
        bindService(intent, serviceConnection, BIND_AUTO_CREATE)
    }

    override fun onStop() {
        super.onStop()
        observationJob?.cancel()
        observationJob = null
        if (isBound) {
            unbindService(serviceConnection)
            isBound = false
        }
    }

    private fun observeDaemonState() {
        observationJob?.cancel()
        observationJob = lifecycleScope.launch {
            repeatOnLifecycle(Lifecycle.State.STARTED) {
                daemonService?.stateFlow?.collect { state ->
                    updateUi(state)
                }
            }
        }
    }

    private fun updateUi(state: PoStState) {
        tvStatus.text = when (state.status) {
            PoStStatus.IDLE -> getString(R.string.status_idle)
            PoStStatus.ALLOCATING_MEMORY -> getString(R.string.status_allocating)
            PoStStatus.PROVING -> getString(R.string.status_proving)
            PoStStatus.PAUSED -> getString(R.string.status_paused)
            PoStStatus.CANCELLED -> getString(R.string.status_cancelled)
            PoStStatus.COMPLETED -> getString(R.string.status_completed)
            PoStStatus.FAILED -> getString(R.string.status_failed)
        }

        val statusColor = when (state.status) {
            PoStStatus.COMPLETED -> "#2E7D32".toColorInt()
            PoStStatus.PROVING, PoStStatus.ALLOCATING_MEMORY -> "#1565C0".toColorInt()
            PoStStatus.PAUSED, PoStStatus.CANCELLED -> "#EF6C00".toColorInt()
            PoStStatus.FAILED -> "#C62828".toColorInt()
            PoStStatus.IDLE -> "#424242".toColorInt()
        }
        tvStatus.setTextColor(statusColor)

        btnStart.isEnabled = !state.isRunning
        btnCancel.isEnabled = state.isRunning
        btnPauseResume.isEnabled = state.isRunning

        if (state.status == PoStStatus.PAUSED) {
            btnPauseResume.text = getString(R.string.btn_resume)
        } else {
            btnPauseResume.text = getString(R.string.btn_pause)
        }

        etRam.isEnabled = !state.isRunning
        etIterations.isEnabled = !state.isRunning

        if ((state.status == PoStStatus.PROVING) || (state.status == PoStStatus.ALLOCATING_MEMORY)) {
            progressBar.visibility = View.VISIBLE
            progressBar.isIndeterminate = (state.status == PoStStatus.ALLOCATING_MEMORY)
        } else {
            progressBar.visibility = View.GONE
        }

        val ramMbDisplay = if (state.allocatedMemoryMb > 0) state.allocatedMemoryMb else (etRam.text.toString().toIntOrNull() ?: 16)
        val ramBytesDisplay = if (state.allocatedRamBytes > 0) state.allocatedRamBytes else (ramMbDisplay.toLong() * 1024 * 1024)
        tvAllocatedRam.text = String.format(Locale.US, "Allocated RAM: %d MB (%d Bytes)", ramMbDisplay, ramBytesDisplay)

        tvHashes.text = String.format(Locale.US, "Completed Hashes: %d / %d", state.completedHashes, state.targetHashes)
        progressBar.progress = state.progressPercent.toInt()
        tvExecutionTime.text = String.format(Locale.US, "Execution Duration: %d ms", state.elapsedTimeMs)
        tvHashRate.text = String.format(Locale.US, "Current Hash Rate: %.2f H/s", state.currentHashRate)

        if (!state.proofHashHex.isNullOrEmpty()) {
            tvProofDigest.text = state.proofHashHex
            tvProofDigest.visibility = View.VISIBLE
        } else {
            tvProofDigest.text = getString(R.string.no_proof_yet)
        }

        if (!state.errorMessage.isNullOrEmpty()) {
            tvErrorMessage.text = String.format("Error: %s", state.errorMessage)
            tvErrorMessage.visibility = View.VISIBLE
        } else {
            tvErrorMessage.visibility = View.GONE
        }
    }

    private fun requestNotificationPermissionIfNeeded() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            if (checkSelfPermission(android.Manifest.permission.POST_NOTIFICATIONS) != PackageManager.PERMISSION_GRANTED) {
                requestPermissions(arrayOf(android.Manifest.permission.POST_NOTIFICATIONS), 101)
            }
        }
    }

    private fun buildUiLayout() {
        val rootScrollView = ScrollView(this).apply {
            layoutParams = LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT,
                LinearLayout.LayoutParams.MATCH_PARENT,
            )
            isFillViewport = true
            setBackgroundColor("#F5F5F7".toColorInt())
        }

        val mainContainer = LinearLayout(this).apply {
            layoutParams = LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT,
                LinearLayout.LayoutParams.WRAP_CONTENT,
            )
            orientation = LinearLayout.VERTICAL
            val pad = dpToPx(16)
            setPadding(pad, pad, pad, pad)
        }

        // Header Card
        val headerCard = createCardView().apply {
            val contentLayout = LinearLayout(this@MainActivity).apply {
                orientation = LinearLayout.VERTICAL
                val pad = dpToPx(16)
                setPadding(pad, pad, pad, pad)

                addView(
                    TextView(this@MainActivity).apply {
                        text = getString(R.string.app_name)
                        setTextSize(TypedValue.COMPLEX_UNIT_SP, 22f)
                        setTypeface(null, Typeface.BOLD)
                        setTextColor("#1C1B1F".toColorInt())
                    },
                )

                addView(
                    TextView(this@MainActivity).apply {
                        text = getString(R.string.label_infrastructure_node)
                        setTextSize(TypedValue.COMPLEX_UNIT_SP, 14f)
                        setTextColor("#49454F".toColorInt())
                    },
                )
            }
            addView(contentLayout)
        }
        mainContainer.addView(headerCard)

        // Wallet & Identity Card
        val identityCard = createCardView().apply {
            val contentLayout = LinearLayout(this@MainActivity).apply {
                orientation = LinearLayout.VERTICAL
                val pad = dpToPx(16)
                setPadding(pad, pad, pad, pad)

                tvAionId = TextView(this@MainActivity).apply {
                    text = "ID: ${walletManager.getShortId()}"
                    setTextSize(TypedValue.COMPLEX_UNIT_SP, 16f)
                    setTypeface(null, Typeface.BOLD)
                    setTextColor("#1C1B1F".toColorInt())
                }
                addView(tvAionId)

                val balanceRow = LinearLayout(this@MainActivity).apply {
                    orientation = LinearLayout.HORIZONTAL
                    gravity = Gravity.CENTER_VERTICAL
                    setPadding(0, dpToPx(4), 0, 0)
                }
                balanceRow.addView(TextView(this@MainActivity).apply {
                    text = "Balance: "
                    setTextColor("#49454F".toColorInt())
                })
                tvBalance = TextView(this@MainActivity).apply {
                    text = "${walletManager.getSimulatedBalance()} AION"
                    setTextColor("#6750A4".toColorInt())
                    setTypeface(null, Typeface.BOLD)
                }
                balanceRow.addView(tvBalance)
                addView(balanceRow)

                val networkRow = LinearLayout(this@MainActivity).apply {
                    orientation = LinearLayout.HORIZONTAL
                    gravity = Gravity.CENTER_VERTICAL
                    setPadding(0, dpToPx(4), 0, 0)
                }
                networkRow.addView(TextView(this@MainActivity).apply {
                    text = "Peers: "
                    setTextColor("#49454F".toColorInt())
                })
                tvPeers = TextView(this@MainActivity).apply {
                    text = "${networkManager.getPeerCount()}"
                    setTextColor("#49454F".toColorInt())
                }
                networkRow.addView(tvPeers)
                addView(networkRow)
            }
            addView(contentLayout)
        }
        mainContainer.addView(identityCard)

        // Configuration & Control Card
        val controlCard = createCardView().apply {
            val contentLayout = LinearLayout(this@MainActivity).apply {
                orientation = LinearLayout.VERTICAL
                val pad = dpToPx(16)
                setPadding(pad, pad, pad, pad)

                val statusRow = LinearLayout(this@MainActivity).apply {
                    orientation = LinearLayout.HORIZONTAL
                    gravity = Gravity.CENTER_VERTICAL
                }
                statusRow.addView(TextView(this@MainActivity).apply {
                    text = getString(R.string.label_status)
                    setTextSize(TypedValue.COMPLEX_UNIT_SP, 16f)
                    setTypeface(null, Typeface.BOLD)
                })
                tvStatus = TextView(this@MainActivity).apply {
                    text = getString(R.string.status_idle)
                    setTextSize(TypedValue.COMPLEX_UNIT_SP, 16f)
                    setTypeface(null, Typeface.BOLD)
                    val padH = dpToPx(8)
                    setPadding(padH, 0, 0, 0)
                }
                statusRow.addView(tvStatus)
                addView(statusRow)

                // RAM Input Label & EditText
                addView(TextView(this@MainActivity).apply {
                    text = getString(R.string.label_ram_alloc)
                    setTextSize(TypedValue.COMPLEX_UNIT_SP, 14f)
                    setPadding(0, dpToPx(12), 0, dpToPx(4))
                })
                etRam = EditText(this@MainActivity).apply {
                    setText(getString(R.string.default_ram_mb))
                    inputType = InputType.TYPE_CLASS_NUMBER
                    setTextSize(TypedValue.COMPLEX_UNIT_SP, 16f)
                }
                addView(etRam)

                // Iterations Input Label & EditText
                addView(TextView(this@MainActivity).apply {
                    text = getString(R.string.label_iterations)
                    setTextSize(TypedValue.COMPLEX_UNIT_SP, 14f)
                    setPadding(0, dpToPx(12), 0, dpToPx(4))
                })
                etIterations = EditText(this@MainActivity).apply {
                    setText(getString(R.string.default_iterations))
                    inputType = InputType.TYPE_CLASS_NUMBER
                    setTextSize(TypedValue.COMPLEX_UNIT_SP, 16f)
                }
                addView(etIterations)

                // Buttons Layout
                val buttonLayout = LinearLayout(this@MainActivity).apply {
                    orientation = LinearLayout.HORIZONTAL
                    setPadding(0, dpToPx(16), 0, 0)
                }

                btnStart = Button(this@MainActivity).apply {
                    text = getString(R.string.btn_start)
                    layoutParams = LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1f)
                    setOnClickListener {
                        val ram = etRam.text.toString().toIntOrNull() ?: 16
                        val iterations = etIterations.text.toString().toIntOrNull() ?: 1000

                        val intent = Intent(this@MainActivity, PoStDaemonService::class.java)
                        startForegroundService(intent)
                        if (!isBound) {
                            bindService(intent, serviceConnection, BIND_AUTO_CREATE)
                        }
                        daemonService?.startPoSt(ram, iterations)
                    }
                }

                btnPauseResume = Button(this@MainActivity).apply {
                    text = "Pause"
                    isEnabled = false
                    layoutParams = LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1f).apply {
                        setMargins(dpToPx(8), 0, 0, 0)
                    }
                    setOnClickListener {
                        if (daemonService?.stateFlow?.value?.status == PoStStatus.PAUSED) {
                            daemonService?.resumePoSt()
                        } else {
                            daemonService?.pausePoSt()
                        }
                    }
                }

                btnCancel = Button(this@MainActivity).apply {
                    text = getString(R.string.btn_cancel)
                    isEnabled = false
                    layoutParams = LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1f).apply {
                        setMargins(dpToPx(8), 0, 0, 0)
                    }
                    setOnClickListener {
                        daemonService?.cancelPoSt()
                    }
                }

                buttonLayout.addView(btnStart)
                buttonLayout.addView(btnPauseResume)
                buttonLayout.addView(btnCancel)
                addView(buttonLayout)
            }
            addView(contentLayout)
        }
        mainContainer.addView(controlCard)

        // Real-Time Metrics Card
        val metricsCard = createCardView().apply {
            val contentLayout = LinearLayout(this@MainActivity).apply {
                orientation = LinearLayout.VERTICAL
                val pad = dpToPx(16)
                setPadding(pad, pad, pad, pad)

                addView(TextView(this@MainActivity).apply {
                    text = getString(R.string.label_real_time_metrics)
                    setTextSize(TypedValue.COMPLEX_UNIT_SP, 18f)
                    setTypeface(null, Typeface.BOLD)
                    setPadding(0, 0, 0, dpToPx(8))
                })

                progressBar = ProgressBar(this@MainActivity, null, android.R.attr.progressBarStyleHorizontal).apply {
                    visibility = View.GONE
                    layoutParams = LinearLayout.LayoutParams(
                        LinearLayout.LayoutParams.MATCH_PARENT,
                        LinearLayout.LayoutParams.WRAP_CONTENT
                    ).apply { setMargins(0, 0, 0, dpToPx(12)) }
                }
                addView(progressBar)

                tvAllocatedRam = TextView(this@MainActivity).apply {
                    text = "Allocated RAM: 0 MB (0 Bytes)"
                    setTextSize(TypedValue.COMPLEX_UNIT_SP, 14f)
                }
                addView(tvAllocatedRam)

                tvHashes = TextView(this@MainActivity).apply {
                    text = "Completed Hashes: 0 / 0"
                    setTextSize(TypedValue.COMPLEX_UNIT_SP, 14f)
                    setPadding(0, dpToPx(4), 0, 0)
                }
                addView(tvHashes)

                tvExecutionTime = TextView(this@MainActivity).apply {
                    text = "Execution Duration: 0 ms"
                    setTextSize(TypedValue.COMPLEX_UNIT_SP, 14f)
                    setPadding(0, dpToPx(4), 0, 0)
                }
                addView(tvExecutionTime)

                tvHashRate = TextView(this@MainActivity).apply {
                    text = "Current Hash Rate: 0.00 H/s"
                    setTextSize(TypedValue.COMPLEX_UNIT_SP, 14f)
                    setPadding(0, dpToPx(4), 0, 0)
                }
                addView(tvHashRate)
            }
            addView(contentLayout)
        }
        mainContainer.addView(metricsCard)

        // Proof Output Card
        val proofCard = createCardView().apply {
            val contentLayout = LinearLayout(this@MainActivity).apply {
                orientation = LinearLayout.VERTICAL
                val pad = dpToPx(16)
                setPadding(pad, pad, pad, pad)

                addView(TextView(this@MainActivity).apply {
                    text = getString(R.string.label_proof_digest)
                    setTextSize(TypedValue.COMPLEX_UNIT_SP, 18f)
                    setTypeface(null, Typeface.BOLD)
                    setPadding(0, 0, 0, dpToPx(8))
                })

                tvProofDigest = TextView(this@MainActivity).apply {
                    text = getString(R.string.no_proof_yet)
                    setTextSize(TypedValue.COMPLEX_UNIT_SP, 13f)
                    setTypeface(Typeface.MONOSPACE)
                    setBackgroundColor("#E0E0E0".toColorInt())
                    val p = dpToPx(8)
                    setPadding(p, p, p, p)
                    setTextIsSelectable(true)
                }
                addView(tvProofDigest)

                tvErrorMessage = TextView(this@MainActivity).apply {
                    visibility = View.GONE
                    setTextSize(TypedValue.COMPLEX_UNIT_SP, 14f)
                    setTextColor("#C62828".toColorInt())
                    setTypeface(null, Typeface.BOLD)
                    setPadding(0, dpToPx(8), 0, 0)
                }
                addView(tvErrorMessage)
            }
            addView(contentLayout)
        }
        mainContainer.addView(proofCard)

        rootScrollView.addView(mainContainer)
        setContentView(rootScrollView)
    }

    private fun createCardView(): CardView {
        return CardView(this).apply {
            val params = LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT,
                LinearLayout.LayoutParams.WRAP_CONTENT,
            )
            params.setMargins(0, 0, 0, dpToPx(16))
            layoutParams = params
            radius = dpToPx(12).toFloat()
            cardElevation = dpToPx(4).toFloat()
            setCardBackgroundColor(Color.WHITE)
        }
    }

    private fun dpToPx(dp: Int): Int {
        return TypedValue.applyDimension(
            TypedValue.COMPLEX_UNIT_DIP,
            dp.toFloat(),
            resources.displayMetrics
        ).toInt()
    }
}
